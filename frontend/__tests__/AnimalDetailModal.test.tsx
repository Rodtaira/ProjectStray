import { Alert } from 'react-native';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { AnimalDetailModal } from '../AnimalDetailModal';
import { Animal } from '../lib/api';

const baseAnimal: Animal = {
  id: 'a1',
  registered_by: 'owner-1',
  species: 'dog',
  sex: 'unknown',
  name: 'Rex',
  description: 'cachorro dócil',
  is_sterilized: false,
  status: 'stray',
  created_at: '2026-01-01T00:00:00Z',
};

function renderModal(overrides: Partial<Parameters<typeof AnimalDetailModal>[0]> = {}) {
  const onClose = jest.fn();
  const onUpdate = jest.fn().mockResolvedValue(undefined);
  const onDelete = jest.fn().mockResolvedValue(undefined);
  render(
    <AnimalDetailModal
      animal={baseAnimal}
      currentUserId="owner-1"
      onClose={onClose}
      onUpdate={onUpdate}
      onDelete={onDelete}
      {...overrides}
    />
  );
  return { onClose, onUpdate, onDelete };
}

describe('AnimalDetailModal', () => {
  it('hides edit/delete actions from non-owners but still shows the animal', () => {
    renderModal({ currentUserId: 'someone-else' });

    expect(screen.getByText('Rex')).toBeTruthy();
    expect(screen.queryByText('Editar descrição')).toBeNull();
    expect(screen.queryByText('Remover cadastro')).toBeNull();
  });

  it('disables sex/status controls for non-owners so pressing them is a no-op', () => {
    const onUpdate = jest.fn().mockResolvedValue(undefined);
    renderModal({ currentUserId: 'someone-else', onUpdate });

    fireEvent.press(screen.getByText('Macho'));
    fireEvent.press(screen.getByText('Adotado'));

    expect(onUpdate).not.toHaveBeenCalled();
  });

  it('shows edit/delete actions to the owner', () => {
    renderModal();

    expect(screen.getByText('Editar descrição')).toBeTruthy();
    expect(screen.getByText('Remover cadastro')).toBeTruthy();
  });

  it('lets the owner change sex, which calls onUpdate with the new value', async () => {
    const { onUpdate } = renderModal();

    fireEvent.press(screen.getByText('Macho'));

    await waitFor(() => expect(onUpdate).toHaveBeenCalledWith('a1', { sex: 'male' }));
  });

  it('lets the owner change status, which calls onUpdate with the new value', async () => {
    const { onUpdate } = renderModal();

    fireEvent.press(screen.getByText('Adotado'));

    await waitFor(() => expect(onUpdate).toHaveBeenCalledWith('a1', { status: 'adopted' }));
  });

  it('saves the trimmed description and exits edit mode', async () => {
    const { onUpdate } = renderModal();

    fireEvent.press(screen.getByText('Editar descrição'));
    fireEvent.changeText(screen.getByDisplayValue('cachorro dócil'), '  cachorro dócil e calmo  ');
    fireEvent.press(screen.getByText('Salvar descrição'));

    await waitFor(() =>
      expect(onUpdate).toHaveBeenCalledWith('a1', { description: 'cachorro dócil e calmo' })
    );
  });

  it('asks for confirmation before deleting, and does nothing if cancelled', () => {
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    const { onDelete } = renderModal();

    fireEvent.press(screen.getByText('Remover cadastro'));

    expect(alertSpy).toHaveBeenCalledWith(
      'Remover cadastro',
      expect.any(String),
      expect.arrayContaining([
        expect.objectContaining({ text: 'Cancelar', style: 'cancel' }),
        expect.objectContaining({ text: 'Remover mesmo assim', style: 'destructive' }),
      ])
    );
    expect(onDelete).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });

  it('deletes the animal once the destructive alert action is confirmed', async () => {
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation((_title, _msg, buttons) => {
      const confirm = buttons?.find((b) => b.text === 'Remover mesmo assim');
      confirm?.onPress?.();
    });
    const { onDelete } = renderModal();

    fireEvent.press(screen.getByText('Remover cadastro'));

    await waitFor(() => expect(onDelete).toHaveBeenCalledWith('a1'));

    alertSpy.mockRestore();
  });

  it('shows an error if the confirmed delete fails', async () => {
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation((_title, _msg, buttons) => {
      const confirm = buttons?.find((b) => b.text === 'Remover mesmo assim');
      confirm?.onPress?.();
    });
    const onDelete = jest.fn().mockRejectedValue(new Error('boom'));
    renderModal({ onDelete });

    fireEvent.press(screen.getByText('Remover cadastro'));

    await waitFor(() => expect(screen.getByText('Não foi possível remover.')).toBeTruthy());

    alertSpy.mockRestore();
  });
});
