"use client"

const shimmerClass =
  "relative overflow-hidden rounded-lg bg-neutral-200/70 before:absolute before:inset-0 before:-translate-x-full before:bg-gradient-to-r before:from-transparent before:via-white/50 before:to-transparent before:animate-[shimmer_1.6s_infinite] motion-reduce:before:animate-none"

const pill = `${shimmerClass} !rounded-full`

function Block({ w, h, round, className = "" }: { w: string; h: string; round?: boolean; className?: string }) {
  return <div className={`${round ? pill : shimmerClass} ${className}`} style={{ width: w, height: h }} />
}

export function HeroSkeleton() {
  return (
    <section className="relative min-h-0 lg:min-h-[100svh] flex items-center bg-neutral-50 px-6 pt-28 pb-16 lg:py-20">
      <div className="mx-auto flex flex-col items-center text-center max-w-[560px] lg:max-w-[640px]">
        <Block w="200px" h="28px" round className="mb-8" />
        <Block w="100%" h="44px" round className="mb-3" />
        <Block w="88%" h="44px" round className="mb-3" />
        <Block w="95%" h="44px" round className="mb-3" />
        <Block w="55%" h="44px" round className="mb-7" />
        <Block w="90%" h="18px" round className="mb-2" />
        <Block w="70%" h="18px" round className="mb-9" />
        <Block w="100%" h="56px" round className="max-w-lg" />
      </div>
    </section>
  )
}

export function FeaturedSkeleton() {
  return (
    <section className="border-t border-neutral-200/60 bg-neutral-50 py-14 px-6">
      <div className="mx-auto max-w-5xl flex flex-col items-center gap-8">
        <Block w="120px" h="14px" round />
        <div className="flex flex-wrap justify-center gap-12">
          {[80, 90, 70, 85, 75, 60].map((w, i) => (
            <Block key={i} w={`${w}px`} h="40px" round />
          ))}
        </div>
      </div>
    </section>
  )
}

export function FeaturesSkeleton() {
  return (
    <section className="bg-white py-20 md:py-28 px-6">
      <div className="mx-auto max-w-5xl text-center">
        <Block w="340px" h="36px" round className="mx-auto mb-4 max-w-[80%]" />
        <Block w="480px" h="18px" round className="mx-auto mb-12 max-w-[90%]" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Block w="100%" h="280px" className="!rounded-2xl" />
          <Block w="100%" h="280px" className="!rounded-2xl" />
          <Block w="100%" h="200px" className="!rounded-2xl" />
          <Block w="100%" h="200px" className="!rounded-2xl" />
        </div>
      </div>
    </section>
  )
}

export function AgenciesSkeleton() {
  return (
    <section className="py-20 md:py-28 px-6">
      <div className="mx-auto max-w-7xl text-center">
        <Block w="300px" h="36px" round className="mx-auto mb-3 max-w-[70%]" />
        <Block w="440px" h="18px" round className="mx-auto mb-10 max-w-[85%]" />
        <div className="flex flex-wrap justify-center gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Block key={i} w="72px" h="72px" className="!rounded-xl" />
          ))}
        </div>
      </div>
    </section>
  )
}

export function TestimonialSkeleton() {
  return (
    <section className="bg-white py-20 md:py-28 px-6">
      <div className="mx-auto max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        <Block w="100%" h="240px" className="!rounded-2xl" />
        <Block w="100%" h="240px" className="!rounded-2xl" />
      </div>
    </section>
  )
}

export function FAQSkeleton() {
  return (
    <section className="py-20 md:py-28 px-6">
      <div className="mx-auto max-w-3xl text-center">
        <Block w="360px" h="36px" round className="mx-auto mb-4 max-w-[80%]" />
        <Block w="500px" h="18px" round className="mx-auto mb-12 max-w-[90%]" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Block key={i} w="100%" h="52px" className="!rounded-xl" />
          ))}
        </div>
      </div>
    </section>
  )
}

export function CTASkeleton() {
  return (
    <section className="bg-neutral-900 py-20 md:py-28 px-6">
      <div className="mx-auto max-w-3xl text-center">
        <Block w="320px" h="36px" round className="mx-auto mb-4 max-w-[70%] !bg-neutral-700" />
        <Block w="460px" h="18px" round className="mx-auto mb-2 max-w-[85%] !bg-neutral-700" />
        <Block w="380px" h="18px" round className="mx-auto mb-8 max-w-[75%] !bg-neutral-700" />
        <Block w="180px" h="44px" round className="mx-auto !bg-neutral-700" />
      </div>
    </section>
  )
}
