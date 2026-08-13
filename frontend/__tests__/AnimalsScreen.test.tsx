import { Alert } from 'react-native';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { AnimalsScreen } from '../AnimalsScreen';
import { Animal } from '../lib/api';

jest.mock('../lib/auth-client', () => ({
  authenticatedFetch: jest.fn((requestFn: (token: string) => unknown) => requestFn('token')),
}));

jest.mock('../lib/api', () => ({
  listAnimals: jest.fn(),
  createAnimal: jest.fn(),
  updateAnimal: jest.fn(),
  deleteAnimal: jest.fn(),
}));

import { createAnimal, deleteAnimal, listAnimals, updateAnimal } from '../lib/api';

const mockListAnimals = listAnimals as jest.Mock;
const mockCreateAnimal = createAnimal as jest.Mock;
const mockUpdateAnimal = updateAnimal as jest.Mock;
const mockDeleteAnimal = deleteAnimal as jest.Mock;

const rex: Animal = {
  id: 'a1',
  registered_by: 'owner-1',
  species: 'dog',
  sex: 'male',
  name: 'Rex',
  description: null,
  is_sterilized: true,
  status: 'stray',
  created_at: '2026-01-01T00:00:00Z',
};

describe('AnimalsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the empty state when there are no animals', async () => {
    mockListAnimals.mockResolvedValue([]);
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByText('Nenhum animal cadastrado ainda.')).toBeTruthy()
    );
  });

  it('renders the fetched animals with name, species and sterilized badge', async () => {
    mockListAnimals.mockResolvedValue([rex]);
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    expect(screen.getByText('Cachorro · Castrado')).toBeTruthy();
    expect(screen.getByText('stray')).toBeTruthy();
  });

  it('stays usable (empty list, no crash) when loading animals fails', async () => {
    mockListAnimals.mockRejectedValue(new Error('network down'));
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByText('Nenhum animal cadastrado ainda.')).toBeTruthy()
    );
  });

  it('adds a newly created animal to the top of the list', async () => {
    mockListAnimals.mockResolvedValue([]);
    mockCreateAnimal.mockResolvedValue({ ...rex, id: 'a2', name: 'Bidu' });
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByText('Nenhum animal cadastrado ainda.')).toBeTruthy()
    );

    fireEvent.press(screen.getByText('+'));
    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() => expect(screen.getByText('Bidu')).toBeTruthy());
    expect(mockCreateAnimal).toHaveBeenCalledWith('token', {
      species: 'dog',
      sex: 'unknown',
      name: null,
      description: null,
    });
  });

  it('opens the detail modal for the tapped animal and reflects an update', async () => {
    mockListAnimals.mockResolvedValue([rex]);
    mockUpdateAnimal.mockResolvedValue({ ...rex, status: 'adopted' });
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    fireEvent.press(screen.getByText('Rex'));

    await waitFor(() => expect(screen.getByText('Remover cadastro')).toBeTruthy());
    fireEvent.press(screen.getByText('Adotado'));

    await waitFor(() => expect(mockUpdateAnimal).toHaveBeenCalledWith('token', 'a1', { status: 'adopted' }));
    expect(screen.getByText('adopted')).toBeTruthy();
  });

  it('removes the animal from the list and closes the modal after a confirmed delete', async () => {
    mockListAnimals.mockResolvedValue([rex]);
    mockDeleteAnimal.mockResolvedValue(undefined);
    render(<AnimalsScreen currentUserId="owner-1" />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    fireEvent.press(screen.getByText('Rex'));
    await waitFor(() => expect(screen.getByText('Remover cadastro')).toBeTruthy());

    const alertSpy = jest
      .spyOn(Alert, 'alert')
      .mockImplementation((_title, _msg, buttons) => {
        buttons?.find((b) => b.text === 'Remover mesmo assim')?.onPress?.();
      });

    fireEvent.press(screen.getByText('Remover cadastro'));

    await waitFor(() => expect(mockDeleteAnimal).toHaveBeenCalledWith('token', 'a1'));
    await waitFor(() =>
      expect(screen.getByText('Nenhum animal cadastrado ainda.')).toBeTruthy()
    );
    expect(screen.queryByText('Remover cadastro')).toBeNull();

    alertSpy.mockRestore();
  });
});
