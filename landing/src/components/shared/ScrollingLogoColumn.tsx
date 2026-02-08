import { MapPin } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Agency } from "@/data/agencies"
import { Marquee } from "./Marquee"

interface ScrollingLogoColumnProps {
  agencies: Agency[]
  speed?: number
  className?: string
}

const ITEM_HEIGHT = 56
const HIGHLIGHT_INDEX = 2

function AgencyItem({ agency, isHighlighted }: { agency: Agency; isHighlighted: boolean }) {
  return (
    <div
      className={cn(
        "flex h-[56px] items-center gap-2 transition-opacity duration-300",
        isHighlighted ? "opacity-100" : "opacity-30"
      )}
      title={agency.name}
    >
      {isHighlighted && (
        <MapPin className="h-3.5 w-3.5 shrink-0 text-rose-500" />
      )}
      <span
        className={cn(
          "text-[14px] whitespace-nowrap",
          isHighlighted
            ? "text-foreground font-semibold"
            : "text-muted-foreground font-medium"
        )}
      >
        {agency.shortName}
      </span>
      <img
        src={agency.logo}
        alt={agency.name}
        className={cn(
          "h-9 w-9 shrink-0 rounded-full object-cover bg-white transition-all duration-300",
          isHighlighted ? "shadow-md ring-2 ring-amber-300" : "shadow-sm"
        )}
        loading="lazy"
      />
    </div>
  )
}

function StaticAgencyItem({ agency, isHighlighted }: { agency: Agency; isHighlighted: boolean }) {
  return (
    <div
      className={cn(
        "flex h-[56px] items-center gap-2.5",
        isHighlighted ? "opacity-100" : "opacity-30"
      )}
      title={agency.name}
    >
      <span className="text-sm text-muted-foreground font-medium">
        {agency.shortName}
      </span>
      <img
        src={agency.logo}
        alt={agency.name}
        className="h-9 w-9 rounded-full object-cover bg-white shadow-sm"
        loading="lazy"
      />
    </div>
  )
}

export function ScrollingLogoColumn({
  agencies,
  speed = 30,
  className,
}: ScrollingLogoColumnProps) {
  return (
    <Marquee
      items={agencies}
      itemHeight={ITEM_HEIGHT}
      direction="down"
      highlightIndex={HIGHLIGHT_INDEX}
      speed={speed}
      className={className}
      innerClassName="items-end"
      renderItem={(agency, index, isHighlighted) => (
        <AgencyItem
          key={`${agency.shortName}-${index}`}
          agency={agency}
          isHighlighted={isHighlighted}
        />
      )}
      renderStaticItem={(agency, _i, isHighlighted) => (
        <StaticAgencyItem
          key={agency.shortName}
          agency={agency}
          isHighlighted={isHighlighted}
        />
      )}
    />
  )
}
