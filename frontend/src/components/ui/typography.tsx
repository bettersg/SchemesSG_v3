import { cn } from "@/lib/utils";

type TypographyProps<T extends React.ElementType> = {
  as?: T;
  className?: string;
  children: React.ReactNode;
} & Omit<React.ComponentPropsWithoutRef<T>, "as" | "className" | "children">;

export function Display<T extends React.ElementType = "h1">({
  as,
  className,
  children,
  ...rest
}: TypographyProps<T>) {
  const Comp = (as || "h1") as React.ElementType;
  return (
    <Comp
      className={cn(
        "font-serif font-bold leading-[1.08] tracking-tight text-5xl lg:text-[4.5rem] xl:text-[5rem]",
        className,
      )}
      {...rest}
    >
      {children}
    </Comp>
  );
}

export function Headline<T extends React.ElementType = "h1">({
  as,
  className,
  children,
  ...rest
}: TypographyProps<T>) {
  const Comp = (as || "h1") as React.ElementType;
  return (
    <Comp
      className={cn(
        "text-2xl font-semibold text-(--schemes-blue-900) sm:text-3xl",
        className,
      )}
      {...rest}
    >
      {children}
    </Comp>
  );
}

export function Title<T extends React.ElementType = "h2">({
  as,
  className,
  children,
  ...rest
}: TypographyProps<T>) {
  const Comp = (as || "h2") as React.ElementType;
  return (
    <Comp
      className={cn(
        "text-base font-semibold text-(--schemes-blue-900)",
        className,
      )}
      {...rest}
    >
      {children}
    </Comp>
  );
}

export function Body<T extends React.ElementType = "p">({
  as,
  className,
  children,
  ...rest
}: TypographyProps<T>) {
  const Comp = (as || "p") as React.ElementType;
  return (
    <Comp
      className={cn("text-sm text-(--schemes-ink-soft)", className)}
      {...rest}
    >
      {children}
    </Comp>
  );
}

export function Label<T extends React.ElementType = "span">({
  as,
  className,
  children,
  ...rest
}: TypographyProps<T>) {
  const Comp = (as || "span") as React.ElementType;
  return (
    <Comp
      className={cn(
        "text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase",
        className,
      )}
      {...rest}
    >
      {children}
    </Comp>
  );
}
