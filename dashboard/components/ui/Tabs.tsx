import { cn } from "./cn";

export interface TabItem<T extends string> {
  value: T;
  label: string;
  /** Optional badge count rendered next to the label. */
  count?: number;
}

export interface TabsProps<T extends string> {
  items: ReadonlyArray<TabItem<T>>;
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function Tabs<T extends string>({
  items,
  value,
  onChange,
  className,
}: TabsProps<T>) {
  return (
    <div role="tablist" className={cn("tabs", className)}>
      {items.map((item) => {
        const selected = item.value === value;
        return (
          <button
            key={item.value}
            role="tab"
            aria-selected={selected}
            className="tab"
            onClick={() => onChange(item.value)}
          >
            {item.label}
            {item.count !== undefined && (
              <span
                style={{
                  marginLeft: 6,
                  fontVariantNumeric: "tabular-nums",
                  opacity: 0.7,
                }}
              >
                {item.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
