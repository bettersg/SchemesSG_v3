export const FilterIcon = ({ size, ...props }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    height={size || 24}
    width={size || 24}
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      d="M5 4H19L14 10.5V20L10 16V10.5L5 4Z"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
);
