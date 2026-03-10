interface SpinnerProps {
  className?: string;
}

function Spinner({ className = "h-4 w-4" }: SpinnerProps) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block animate-spin rounded-full border-2 border-current border-r-transparent ${className}`}
    />
  );
}

export default Spinner;
