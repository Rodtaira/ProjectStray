import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { CreateSightingModal } from '../CreateSightingModal';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('CreateSightingModal', () => {
  it('submits the trimmed description typed by the user', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    render(<CreateSightingModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.changeText(
      screen.getByPlaceholderText('Ex: cachorro caramelo, parece perdido'),
      '  cachorro caramelo  '
    );
    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith('cachorro caramelo'));
  });

  it('shows an error and keeps the form open when submit fails', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('network down'));
    render(<CreateSightingModal visible onCancel={jest.fn()} onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(
        screen.getByText('Não foi possível salvar o relato. Tente de novo.')
      ).toBeTruthy()
    );
  });

  it('calls onCancel when the cancel button is pressed', () => {
    const onCancel = jest.fn();
    render(<CreateSightingModal visible onCancel={onCancel} onSubmit={jest.fn()} />);

    fireEvent.press(screen.getByText('Cancelar'));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('disables the cancel button while a submission is in flight', async () => {
    const { promise, resolve } = deferred<void>();
    const onSubmit = jest.fn().mockReturnValue(promise);
    const onCancel = jest.fn();
    render(<CreateSightingModal visible onCancel={onCancel} onSubmit={onSubmit} />);

    fireEvent.press(screen.getByText('Salvar'));
    // Enquanto o submit está em voo o botão Cancelar fica desabilitado,
    // então este press não deve disparar onCancel.
    fireEvent.press(screen.getByText('Cancelar'));
    expect(onCancel).not.toHaveBeenCalled();

    resolve();
    await waitFor(() => expect(screen.getByText('Cancelar')).toBeTruthy());

    fireEvent.press(screen.getByText('Cancelar'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
