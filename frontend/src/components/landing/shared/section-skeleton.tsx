"use client";

const shimmerClass =
  "relative overflow-hidden rounded-lg bg-neutral-200/70 before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.6s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/50 before:to-transparent motion-reduce:before:animate-none";

const pill = `${shimmerClass} !rounded-full`;

function Block({
  w,
  h,
  round,
  className = "",
}: {
  w: string;
  h: string;
  round?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`${round ? pill : shimmerClass} ${className}`}
      style={{ width: w, height: h }}
    />
  );
}

function HeroSideColumn({ align = "start" }: { align?: "start" | "end" }) {
  return (
    <div
      className={`hidden h-[520px] items-center lg:flex ${
        align === "end" ? "justify-end" : "justify-start"
      }`}
    >
      <div className="flex w-[168px] flex-col gap-3 overflow-hidden">
        {Array.from({ length: 7 }).map((_, index) => (
          <Block
            key={index}
            w={index % 2 ? "132px" : "156px"}
            h={index % 3 ? "44px" : "52px"}
            round
            className={align === "end" ? "self-end" : ""}
          />
        ))}
      </div>
    </div>
  );
}

function FeatureCardSkeleton({
  illustrationHeight,
}: {
  illustrationHeight: string;
}) {
  return (
    <div className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6">
      <Block w="100%" h={illustrationHeight} className="!rounded-xl" />
      <Block w="62%" h="24px" round className="mt-5" />
      <Block w="100%" h="16px" round className="mt-3" />
      <Block w="86%" h="16px" round className="mt-2" />
    </div>
  );
}

export function HeroSkeleton() {
  return (
    <section className="grain-overlay relative flex min-h-0 items-center overflow-hidden bg-neutral-50 lg:min-h-[100svh]">
      <div className="pointer-events-none absolute bottom-[10%] left-[10%] h-[600px] w-[600px] rounded-full bg-amber-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute top-[10%] right-[5%] h-[600px] w-[600px] rounded-full bg-blue-300/20 blur-[120px]" />

      <div className="relative mx-auto grid w-full max-w-7xl grid-cols-1 gap-8 px-6 pt-28 pb-16 lg:grid-cols-[200px_1fr_200px] lg:py-20">
        <HeroSideColumn />
        <div className="z-10 flex flex-col items-center justify-center px-4 text-center md:px-8">
          <Block w="100%" h="64px" round className="max-w-[680px]" />
          <Block w="78%" h="64px" round className="mt-3 max-w-[540px]" />
          <Block w="88%" h="22px" round className="mt-5 max-w-xl" />
          <Block w="70%" h="22px" round className="mt-2 max-w-lg" />
          <div className="mt-8 flex w-full max-w-lg flex-col gap-8">
            <Block w="100%" h="58px" round />
            <div className="flex flex-wrap justify-center gap-2">
              {Array.from({ length: 10 }).map((_, index) => (
                <Block
                  key={index}
                  w={index % 3 === 0 ? "132px" : "108px"}
                  h="46px"
                  round
                />
              ))}
            </div>
          </div>
        </div>
        <HeroSideColumn align="end" />
      </div>
    </section>
  );
}

export function FeaturedSkeleton() {
  return (
    <section className="border-t border-neutral-200/60 bg-neutral-50 px-6 py-14">
      <div className="mx-auto max-w-5xl">
        <Block w="170px" h="16px" round className="mx-auto mb-10" />
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-8 md:gap-x-8">
          {[120, 132, 108, 104, 128, 88].map((w, index) => (
            <Block
              key={index}
              w={`${w}px`}
              h={index === 3 ? "44px" : "64px"}
              round
            />
          ))}
        </div>

        <div className="mt-10 border-t border-neutral-100 pt-10">
          <Block w="190px" h="16px" round className="mx-auto mb-10" />
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
            <Block w="168px" h="64px" round />
            <Block w="150px" h="64px" round />
          </div>
        </div>
      </div>
    </section>
  );
}

export function FeaturesSkeleton() {
  return (
    <section className="overflow-hidden bg-neutral-50 px-6 py-20 md:py-28">
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <Block
            w="420px"
            h="44px"
            round
            className="mx-auto max-w-[82%]"
          />
          <Block
            w="600px"
            h="22px"
            round
            className="mx-auto mt-4 max-w-[90%]"
          />
        </div>

        <div className="relative mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-5 md:grid-cols-2">
          <div className="relative z-10 flex flex-col gap-5">
            <FeatureCardSkeleton illustrationHeight="218px" />
            <FeatureCardSkeleton illustrationHeight="214px" />
          </div>
          <div className="relative z-10 flex flex-col gap-5">
            <FeatureCardSkeleton illustrationHeight="200px" />
            <FeatureCardSkeleton illustrationHeight="164px" />
          </div>
        </div>
      </div>
    </section>
  );
}

export function AgenciesSkeleton() {
  return (
    <section className="bg-neutral-50 px-6 py-10">
      <div className="mx-auto max-w-5xl overflow-hidden rounded-3xl bg-white pt-16 pb-0">
        <div className="px-6 text-center">
          <Block
            w="460px"
            h="44px"
            round
            className="mx-auto max-w-[86%]"
          />
          <Block
            w="560px"
            h="22px"
            round
            className="mx-auto mt-4 max-w-[90%]"
          />
          <Block w="180px" h="56px" round className="mx-auto mt-7" />
        </div>

        <div className="mt-10 flex flex-col gap-4 overflow-hidden pb-10">
          {Array.from({ length: 3 }).map((_, row) => (
            <div
              key={row}
              className={`flex gap-4 ${row % 2 ? "-ml-12" : "ml-4"}`}
            >
              {Array.from({ length: 7 }).map((__, index) => (
                <Block
                  key={index}
                  w={index % 2 ? "126px" : "148px"}
                  h="52px"
                  round
                  className="shrink-0"
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function TestimonialSkeleton() {
  return (
    <section className="bg-white px-6 py-20 md:py-28">
      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-8 md:grid-cols-2 lg:gap-12">
        {Array.from({ length: 2 }).map((_, index) => (
          <div
            key={index}
            className="flex min-h-[236px] flex-col rounded-2xl border border-neutral-200/60 bg-neutral-50/50 p-8 lg:p-10"
          >
            <Block w="100%" h="18px" round />
            <Block w="92%" h="18px" round className="mt-3" />
            <Block w="72%" h="18px" round className="mt-3" />
            <div className="mt-auto flex items-center gap-3 pt-6">
              <Block w="40px" h="40px" round />
              <div className="flex-1">
                <Block w="150px" h="16px" round />
                <Block w="110px" h="12px" round className="mt-2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function FAQSkeleton() {
  return (
    <section className="bg-neutral-50/60 px-6 py-20 md:py-28">
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <Block
            w="360px"
            h="44px"
            round
            className="mx-auto max-w-[80%]"
          />
          <Block
            w="520px"
            h="22px"
            round
            className="mx-auto mt-4 max-w-[90%]"
          />
        </div>

        <div className="mx-auto mt-14 grid max-w-5xl grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
          <div className="flex flex-col gap-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Block key={index} w="100%" h="66px" className="!rounded-xl" />
            ))}
          </div>
          <div className="flex">
            <div className="flex min-h-[320px] flex-1 flex-col rounded-2xl border border-neutral-200/80 bg-white p-8 shadow-sm">
              <div className="mb-6 flex items-start gap-2">
                <Block w="80px" h="56px" className="!rounded-lg" />
                <Block w="32px" h="32px" className="mt-4 -ml-3 !rounded-lg" />
              </div>
              <Block w="78%" h="24px" round />
              <Block w="100%" h="16px" round className="mt-4" />
              <Block w="84%" h="16px" round className="mt-2" />
              <Block w="100%" h="52px" round className="mt-auto" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function CTASkeleton() {
  return (
    <section className="relative overflow-hidden bg-neutral-950 px-6 py-24">
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-amber-400/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-20 right-[10%] h-[300px] w-[300px] rounded-full bg-blue-400/5 blur-[80px]" />
      <div className="relative mx-auto max-w-2xl text-center">
        <Block
          w="520px"
          h="52px"
          round
          className="mx-auto max-w-[86%] !bg-neutral-700"
        />
        <Block
          w="500px"
          h="22px"
          round
          className="mx-auto mt-5 max-w-[90%] !bg-neutral-700"
        />
        <Block
          w="340px"
          h="22px"
          round
          className="mx-auto mt-2 max-w-[72%] !bg-neutral-700"
        />
        <Block
          w="190px"
          h="56px"
          round
          className="mx-auto mt-9 !bg-neutral-700"
        />
        <Block
          w="220px"
          h="16px"
          round
          className="mx-auto mt-4 !bg-neutral-700"
        />
      </div>
    </section>
  );
}
