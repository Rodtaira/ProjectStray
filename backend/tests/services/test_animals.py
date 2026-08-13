import uuid

from app.models.animal import AnimalSex, AnimalSpecies, AnimalStatus
from app.schemas.animal import AnimalCreate, AnimalUpdate
from app.services import animals as animals_service


async def test_create_animal_persists_with_the_reporter_and_defaults(db_session, make_user):
    user = await make_user()
    data = AnimalCreate(species="dog")

    animal = await animals_service.create_animal(db_session, data, registered_by=user.id)

    assert animal.id is not None
    assert animal.registered_by == user.id
    assert animal.species == AnimalSpecies.dog
    assert animal.sex == AnimalSex.unknown
    assert animal.status == AnimalStatus.stray
    assert animal.is_sterilized is False


async def test_get_animal_by_id_returns_none_when_missing(db_session):
    assert await animals_service.get_animal_by_id(db_session, uuid.uuid4()) is None


async def test_get_animal_by_id_finds_an_existing_animal(db_session, make_user, make_animal):
    user = await make_user()
    animal = await make_animal(registered_by=user.id)

    found = await animals_service.get_animal_by_id(db_session, animal.id)

    assert found is not None
    assert found.id == animal.id


class TestListAnimals:
    async def test_orders_by_most_recently_created_first(self, db_session, make_user, make_animal):
        # Postgres `now()` reflete o início da transação, não do statement —
        # dois INSERTs na mesma sessão de teste teriam o mesmo created_at se
        # a gente não fixasse valores explícitos e distintos aqui.
        import datetime as dt

        user = await make_user()
        first = await make_animal(
            registered_by=user.id,
            name="Primeiro",
            created_at=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        second = await make_animal(
            registered_by=user.id,
            name="Segundo",
            created_at=dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc),
        )

        result = await animals_service.list_animals(db_session)

        ids_in_order = [a.id for a in result]
        assert ids_in_order.index(second.id) < ids_in_order.index(first.id)

    async def test_respects_the_limit(self, db_session, make_user, make_animal):
        user = await make_user()
        for _ in range(3):
            await make_animal(registered_by=user.id)

        result = await animals_service.list_animals(db_session, limit=2)

        assert len(result) == 2

    async def test_filters_by_species(self, db_session, make_user, make_animal):
        user = await make_user()
        dog = await make_animal(registered_by=user.id, species=AnimalSpecies.dog)
        await make_animal(registered_by=user.id, species=AnimalSpecies.cat)

        result = await animals_service.list_animals(db_session, species="dog")

        assert [a.id for a in result] == [dog.id]

    async def test_filters_by_status(self, db_session, make_user, make_animal):
        user = await make_user()
        adopted = await make_animal(registered_by=user.id, status=AnimalStatus.adopted)
        await make_animal(registered_by=user.id, status=AnimalStatus.stray)

        result = await animals_service.list_animals(db_session, status="adopted")

        assert [a.id for a in result] == [adopted.id]

    async def test_combines_species_and_status_filters(self, db_session, make_user, make_animal):
        user = await make_user()
        match = await make_animal(
            registered_by=user.id, species=AnimalSpecies.cat, status=AnimalStatus.adopted
        )
        await make_animal(
            registered_by=user.id, species=AnimalSpecies.dog, status=AnimalStatus.adopted
        )
        await make_animal(
            registered_by=user.id, species=AnimalSpecies.cat, status=AnimalStatus.stray
        )

        result = await animals_service.list_animals(db_session, species="cat", status="adopted")

        assert [a.id for a in result] == [match.id]


class TestUpdateAnimal:
    async def test_updates_only_the_provided_fields(self, db_session, make_user, make_animal):
        user = await make_user()
        animal = await make_animal(
            registered_by=user.id, name="Rex", description="dócil", sex=AnimalSex.male
        )

        updated = await animals_service.update_animal(
            db_session, animal, AnimalUpdate(description="dócil e brincalhão")
        )

        assert updated.name == "Rex"
        assert updated.sex == AnimalSex.male
        assert updated.description == "dócil e brincalhão"

    async def test_updates_sterilization_and_status(self, db_session, make_user, make_animal):
        user = await make_user()
        animal = await make_animal(registered_by=user.id)

        updated = await animals_service.update_animal(
            db_session,
            animal,
            AnimalUpdate(is_sterilized=True, status="adopted"),
        )

        assert updated.is_sterilized is True
        assert updated.status == AnimalStatus.adopted


async def test_delete_animal_removes_it(db_session, make_user, make_animal):
    user = await make_user()
    animal = await make_animal(registered_by=user.id)

    await animals_service.delete_animal(db_session, animal)

    assert await animals_service.get_animal_by_id(db_session, animal.id) is None


def test_to_read_schema_maps_enum_values_to_their_plain_strings():
    import datetime as dt

    from app.models.animal import Animal

    animal = Animal(
        id=uuid.uuid4(),
        registered_by=uuid.uuid4(),
        species=AnimalSpecies.cat,
        sex=AnimalSex.female,
        name="Mimi",
        description=None,
        is_sterilized=True,
        status=AnimalStatus.in_shelter,
        created_at=dt.datetime.now(dt.timezone.utc),
    )

    schema = animals_service.to_read_schema(animal)

    assert schema.species == "cat"
    assert schema.sex == "female"
    assert schema.status == "in_shelter"
    assert schema.name == "Mimi"
