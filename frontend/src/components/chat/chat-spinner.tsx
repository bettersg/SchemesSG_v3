import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import { cn } from "@/lib/utils";

type ChatSpinnerProps = {
  className?: string;
};

export default function ChatSpinner({ className }: ChatSpinnerProps) {
  return (
    <DotLottieReact
      className={cn("size-8", className)}
      src="https://lottie.host/f16d88bc-aee3-4c2f-b50f-fa9f3750e242/je06uPGeC8.lottie"
      loop
      autoplay
    />
  );
}
