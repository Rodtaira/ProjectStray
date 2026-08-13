import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { SightingDetailModal } from '../SightingDetailModal';
import { Sighting } from '../lib/api';

const baseSighting: Sighting = {
  id: 's1',
  reporter_id: 'owner-1',
  description: 'cachorro caramelo',
  status: 'open',
  latitude: -15.7,
  longitude: -47.9,
  created_at: '2026-01-01T00:00:00Z',
};

describe('SightingDetailModal', () => {
  it('hides edit/resolve controls from users who are not the reporter', () => {
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="someone-else"
        onClose={jest.fn()}
        onUpdate={jest.fn()}
      />
    );

    expect(screen.queryByText('Editar descrição')).toBeNull();
    expect(screen.queryByText('Marcar como resolvido')).toBeNull();
  });

  it('shows edit/resolve controls to the reporter', () => {
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="owner-1"
        onClose={jest.fn()}
        onUpdate={jest.fn()}
      />
    );

    expect(screen.getByText('Editar descrição')).toBeTruthy();
    expect(screen.getByText('Marcar como resolvido')).toBeTruthy();
  });

  it('saves the trimmed description and exits edit mode on success', async () => {
    const onUpdate = jest.fn().mockResolvedValue(undefined);
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="owner-1"
        onClose={jest.fn()}
        onUpdate={onUpdate}
      />
    );

    fireEvent.press(screen.getByText('Editar descrição'));
    fireEvent.changeText(screen.getByDisplayValue('cachorro caramelo'), '  vira-lata caramelo  ');
    fireEvent.press(screen.getByText('Salvar descrição'));

    await waitFor(() =>
      expect(onUpdate).toHaveBeenCalledWith('s1', { description: 'vira-lata caramelo' })
    );
    await waitFor(() => expect(screen.getByText('Editar descrição')).toBeTruthy());
  });

  it('shows an error and stays in edit mode when saving the description fails', async () => {
    const onUpdate = jest.fn().mockRejectedValue(new Error('boom'));
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="owner-1"
        onClose={jest.fn()}
        onUpdate={onUpdate}
      />
    );

    fireEvent.press(screen.getByText('Editar descrição'));
    fireEvent.press(screen.getByText('Salvar descrição'));

    await waitFor(() => expect(screen.getByText('Não foi possível salvar.')).toBeTruthy());
    expect(screen.getByText('Salvar descrição')).toBeTruthy();
  });

  it('toggles an open sighting to resolved', async () => {
    const onUpdate = jest.fn().mockResolvedValue(undefined);
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="owner-1"
        onClose={jest.fn()}
        onUpdate={onUpdate}
      />
    );

    fireEvent.press(screen.getByText('Marcar como resolvido'));

    await waitFor(() => expect(onUpdate).toHaveBeenCalledWith('s1', { status: 'resolved' }));
  });

  it('toggles a resolved sighting back to open', async () => {
    const onUpdate = jest.fn().mockResolvedValue(undefined);
    render(
      <SightingDetailModal
        sighting={{ ...baseSighting, status: 'resolved' }}
        currentUserId="owner-1"
        onClose={jest.fn()}
        onUpdate={onUpdate}
      />
    );

    expect(screen.getByText('Resolvido')).toBeTruthy();
    fireEvent.press(screen.getByText('Reabrir'));

    await waitFor(() => expect(onUpdate).toHaveBeenCalledWith('s1', { status: 'open' }));
  });

  it('calls onClose when the close button is pressed', () => {
    const onClose = jest.fn();
    render(
      <SightingDetailModal
        sighting={baseSighting}
        currentUserId="owner-1"
        onClose={onClose}
        onUpdate={jest.fn()}
      />
    );

    fireEvent.press(screen.getByText('Fechar'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
