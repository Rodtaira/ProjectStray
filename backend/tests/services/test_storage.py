from app.core.config import settings
from app.services import storage


class FakeS3Client:
    def __init__(self):
        self.put_calls = []
        self.get_responses = {}
        self.delete_calls = []

    def put_object(self, Bucket, Key, Body, ContentType):
        self.put_calls.append(
            {"Bucket": Bucket, "Key": Key, "Body": Body, "ContentType": ContentType}
        )

    def get_object(self, Bucket, Key):
        return {"Body": _FakeBody(self.get_responses[Key])}

    def delete_object(self, Bucket, Key):
        self.delete_calls.append({"Bucket": Bucket, "Key": Key})


class _FakeBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class TestUploadBytes:
    def test_sends_the_bytes_to_the_configured_bucket_with_the_right_key(self, monkeypatch):
        fake = FakeS3Client()
        monkeypatch.setattr(storage, "_s3", fake)

        storage.upload_bytes("animals/x/photo.jpg", b"fake-image-bytes", "image/jpeg")

        assert len(fake.put_calls) == 1
        call = fake.put_calls[0]
        assert call["Bucket"] == settings.s3_bucket_name
        assert call["Key"] == "animals/x/photo.jpg"
        assert call["Body"] == b"fake-image-bytes"
        assert call["ContentType"] == "image/jpeg"


class TestGetBytes:
    def test_returns_the_object_bytes_for_the_given_key(self, monkeypatch):
        fake = FakeS3Client()
        fake.get_responses["animals/x/photo.jpg"] = b"fake-image-bytes"
        monkeypatch.setattr(storage, "_s3", fake)

        result = storage.get_bytes("animals/x/photo.jpg")

        assert result == b"fake-image-bytes"


class TestDeleteObject:
    def test_deletes_the_object_by_key(self, monkeypatch):
        fake = FakeS3Client()
        monkeypatch.setattr(storage, "_s3", fake)

        storage.delete_object("animals/x/photo.jpg")

        assert fake.delete_calls == [{"Bucket": settings.s3_bucket_name, "Key": "animals/x/photo.jpg"}]