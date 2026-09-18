import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ActionLink, Button } from '../src/components/ui';
import { AccountForm } from '../src/components/account-form';

describe('shared controls', () => {
  it('requires an explicit submit type and blocks a loading action', () => {
    const submit = vi.fn((event: React.FormEvent) => event.preventDefault());
    const click = vi.fn();
    render(<form onSubmit={submit}><Button>Secondary action</Button><Button type="submit">Save</Button><Button loading onClick={click}>Working</Button></form>);
    fireEvent.click(screen.getByRole('button', { name: 'Secondary action' }));
    expect(submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(submit).toHaveBeenCalledOnce();
    const working = screen.getByRole('button', { name: 'Working' });
    expect(working).toBeDisabled();
    expect(working).toHaveAttribute('aria-busy', 'true');
    fireEvent.click(working);
    expect(click).not.toHaveBeenCalled();
  });
  it('keeps navigation as a real link with caller-provided accessible props', () => {
    render(<ActionLink href="/hesap" aria-label="Account settings" variant="secondary">Account</ActionLink>);
    expect(screen.getByRole('link', { name: 'Account settings' })).toHaveAttribute('href', '/hesap');
  });
  it('keeps repeated fields uniquely associated with help in separate forms', () => {
    const fields = [{ name: 'password', label: 'Şifre', type: 'password', password: true }];
    render(<><AccountForm title="First" path="first" fields={fields} submit="Save first" /><AccountForm title="Second" path="second" fields={fields} submit="Save second" /></>);
    const inputs = screen.getAllByLabelText('Şifre');
    expect(inputs[0].id).not.toEqual(inputs[1].id);
    for (const input of inputs) {
      expect(input).toBeRequired();
      expect(input).toHaveAttribute('autocomplete', 'new-password');
      expect(input).toHaveAccessibleDescription(/8–20 karakter/);
    }
  });
});
