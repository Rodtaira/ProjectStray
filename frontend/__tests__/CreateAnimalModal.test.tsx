import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { CreateAnimalModal } from '../CreateAnimalModal';

describe('CreateAnimalModal', () => {
  it('defaults to dog/unknown and submits trimmed name/description as null when left blank', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    render(<CreateAnimalModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        species: 'dog',
        sex: 'unknown',
        name: null,
        description: null,
      })
    );
  });

  it('trims whitespace-only name/description down to null', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    render(<CreateAnimalModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Nome (opcional)'), '   ');
    fireEvent.changeText(
      screen.getByPlaceholderText('Descrição (cor, porte, características)'),
      '   '
    );
    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ name: null, description: null })
      )
    );
  });

  it('submits the selected species and sex after switching segments', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    render(<CreateAnimalModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Gato'));
    fireEvent.press(screen.getByText('Fêmea'));
    fireEvent.changeText(screen.getByPlaceholderText('Nome (opcional)'), 'Mimi');
    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ species: 'cat', sex: 'female', name: 'Mimi' })
      )
    );
  });

  it('shows an error message when the submit fails', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('boom'));
    render(<CreateAnimalModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(screen.getByText('Não foi possível salvar. Tente de novo.')).toBeTruthy()
    );
  });

  it('calls onCancel when cancel is pressed', () => {
    const onCancel = jest.fn();
    render(<CreateAnimalModal visible onCancel={onCancel} onSubmit={jest.fn()} />);

    fireEvent.press(screen.getByText('Cancelar'));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
