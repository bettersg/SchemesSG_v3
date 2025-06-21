export const HamburgerIcon = ({ size, ...props }) => (
  <svg
    aria-hidden="true"
    fill="none"
    focusable="false"
    height={size || 24}
    width={size || 24}
    role="presentation"
    viewBox="0 0 24 24"
    {...props}
  >
    <path
      d="M4 6h16M4 12h16M4 18h16"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);
