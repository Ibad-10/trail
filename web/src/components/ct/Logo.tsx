export function Logo() {
  return (
    <span className="flex items-center gap-2">
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 6 L12 18 L19 6" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="5" cy="6" r="2.6" fill="var(--close)" />
        <circle cx="12" cy="18" r="2.6" fill="var(--rfi)" />
        <circle cx="19" cy="6" r="2.6" fill="var(--esc)" />
      </svg>
      <span className="font-serif text-xl leading-none tracking-tight">ControlTrail</span>
    </span>
  );
}
