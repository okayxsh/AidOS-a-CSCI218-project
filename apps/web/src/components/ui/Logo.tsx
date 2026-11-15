interface LogoProps {
  /** Render only the mark, e.g. in the collapsed dashboard header. */
  markOnly?: boolean;
}

/** AidOS mark: an "A" inside a rounded frame; the crossbar is the allocation line. */
export function Logo({ markOnly = false }: LogoProps) {
  return (
    <span className="logo">
      <svg
        className="logo__mark"
        width="28"
        height="28"
        viewBox="0 0 28 28"
        fill="none"
        aria-hidden="true"
      >
        <rect x="1" y="1" width="26" height="26" rx="8" stroke="var(--teal)" strokeWidth="1.6" />
        <path
          d="M8 19.5 14 7.5l6 12"
          stroke="var(--text)"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M10.4 15h7.2" stroke="var(--teal)" strokeWidth="1.9" strokeLinecap="round" />
      </svg>
      {markOnly ? (
        <span className="visually-hidden">AidOS</span>
      ) : (
        <span className="logo__word">AidOS</span>
      )}
    </span>
  );
}
