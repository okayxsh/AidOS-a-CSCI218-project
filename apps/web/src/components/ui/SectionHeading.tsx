import type { ReactNode } from 'react';

interface SectionHeadingProps {
  id: string;
  title: ReactNode;
  lede?: ReactNode;
  align?: 'start' | 'center';
}

/** Landing section heading. The heading carries its own weight: no eyebrow label. */
export function SectionHeading({ id, title, lede, align = 'start' }: SectionHeadingProps) {
  return (
    <header className={`section-heading section-heading--${align}`}>
      <h2 id={id}>{title}</h2>
      {lede && <p className="section-heading__lede">{lede}</p>}
    </header>
  );
}
