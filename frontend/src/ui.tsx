import type { ReactNode } from 'react';

export const primaryButton =
  'inline-flex h-11 cursor-pointer items-center justify-center rounded-[10px] bg-accent px-4 text-sm leading-5 text-white outline-accent focus-visible:outline-2 focus-visible:outline-offset-2';

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
