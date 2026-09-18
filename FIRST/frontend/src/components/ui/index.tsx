import Link from 'next/link';
import type { ComponentProps, HTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'quiet' | 'danger';
function classes(...values: (string | undefined | false)[]) { return values.filter(Boolean).join(' '); }

export function Button({ variant = 'primary', loading = false, type = 'button', className, disabled, ...props }: ComponentProps<'button'> & { variant?: Variant; loading?: boolean }) {
  return <button {...props} type={type} disabled={disabled || loading} aria-busy={loading || props['aria-busy']} className={classes('button', `button--${variant}`, className)} />;
}
export function ActionLink({ variant = 'primary', className, ...props }: ComponentProps<typeof Link> & { variant?: Variant }) {
  return <Link {...props} className={classes('button', `button--${variant}`, className)} />;
}
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={classes('input', className)} />;
}
export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={classes('input', className)} />;
}
export function Checkbox({ children, className, ...props }: Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & { children: ReactNode }) {
  return <label className={classes('check', className)}><input {...props} type="checkbox" /> <span>{children}</span></label>;
}
export function Field({ id, label, help, error, children, className }: { id: string; label: string; help?: ReactNode; error?: ReactNode; children: ReactNode; className?: string }) {
  return <div className={classes('field', className)}><label htmlFor={id}>{label}</label>{children}
    {help && <p className="field-help" id={`${id}-help`}>{help}</p>}
    {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
  </div>;
}
export function Alert({ tone = 'info', className, ...props }: HTMLAttributes<HTMLDivElement> & { tone?: 'info' | 'error' | 'success' }) {
  return <div {...props} className={classes('alert', `alert--${tone}`, className)} />;
}
export function Surface({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <section {...props} className={classes('surface', className)} />;
}
export function PageHeading({ title, description, eyebrow = 'FIRST / HESAP' }: { title: string; description?: string; eyebrow?: string }) {
  return <div className="page-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>;
}
