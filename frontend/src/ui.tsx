import { cloneElement, useEffect, useId, useRef, type ReactElement, type ReactNode } from 'react';

export const primaryButton =
  'inline-flex h-11 cursor-pointer items-center justify-center rounded-[10px] bg-accent px-4 text-sm leading-5 text-white outline-accent focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-default disabled:bg-line disabled:text-muted';

export const secondaryButton =
  'inline-flex h-11 cursor-pointer items-center justify-center rounded-[10px] border border-line bg-white px-4 text-sm leading-5 text-ink outline-accent hover:bg-page focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-default disabled:text-muted disabled:hover:bg-white';

export const dangerButton =
  'inline-flex h-11 cursor-pointer items-center justify-center rounded-[10px] bg-danger px-4 text-sm leading-5 text-white outline-danger focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-default disabled:bg-line disabled:text-muted';

export const inputClass =
  'h-12 w-full rounded-[10px] border border-line bg-white px-3 text-sm leading-[22px] text-ink outline-none focus:border-accent focus:ring-3 focus:ring-accent/20 aria-invalid:border-danger aria-invalid:focus:ring-danger/20';

interface FormFieldProps {
  label: string;
  error?: string;
  className?: string;
  children: ReactElement<{ id?: string; 'aria-invalid'?: boolean; 'aria-describedby'?: string }>;
}

export function FormField({ label, error, className = '', children }: FormFieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <label htmlFor={id} className="text-sm leading-5 text-muted">
        {label}
      </label>
      {cloneElement(children, {
        id,
        'aria-invalid': error ? true : undefined,
        'aria-describedby': error ? errorId : undefined,
      })}
      {error && (
        <p id={errorId} className="text-xs leading-[18px] text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  confirmLabel: string;
  cancelLabel: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children: ReactNode;
}

export function ConfirmDialog({ open, title, confirmLabel, cancelLabel, busy, onConfirm, onCancel, children }: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
      className="m-auto w-[calc(100%-32px)] max-w-[560px] rounded-2xl bg-white p-6 text-ink backdrop:bg-ink/40 sm:p-8"
    >
      <h2 id={titleId} className="text-[22px] leading-[30px] font-bold">
        {title}
      </h2>
      <div className="mt-6">{children}</div>
      <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row">
        <button type="button" autoFocus disabled={busy} onClick={onCancel} className={`${secondaryButton} sm:flex-1`}>
          {cancelLabel}
        </button>
        <button type="button" disabled={busy} onClick={onConfirm} className={`${dangerButton} sm:flex-1`}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}

export function Notice({ title, text }: { title: string; text: string }) {
  return (
    <div role="alert" className="flex flex-col gap-1 rounded-xl border border-line bg-error-soft p-4">
      <p className="text-sm leading-5 text-ink">{title}</p>
      <p className="text-xs leading-[18px] text-muted">{text}</p>
    </div>
  );
}

export function plural(count: number, forms: [string, string, string]) {
  const tens = count % 100;
  const units = count % 10;
  if (tens >= 11 && tens <= 14) return forms[2];
  if (units === 1) return forms[0];
  if (units >= 2 && units <= 4) return forms[1];
  return forms[2];
}

interface StatePanelProps {
  title: string;
  text: string;
  alert?: boolean;
  children?: ReactNode;
}

export function StatePanel({ title, text, alert, children }: StatePanelProps) {
  return (
    <section
      role={alert ? 'alert' : undefined}
      className="flex min-h-80 flex-col items-center gap-4 rounded-2xl border border-line bg-white px-8 pt-24 pb-8 text-center"
    >
      <h2 className="text-[22px] leading-[30px] font-bold">{title}</h2>
      <p className="max-w-[461px] text-sm leading-[22px] text-muted">{text}</p>
      {children && <div className="mt-2">{children}</div>}
    </section>
  );
}
