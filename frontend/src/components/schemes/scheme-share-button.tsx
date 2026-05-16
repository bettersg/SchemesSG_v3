import { Button } from "@heroui/react";
import { ForwardIcon } from "lucide-react";

interface SchemeShareButtonProps {
  title: string;
  text: string;
  link: string;
}

function SchemeShareButton({ title, text, link }: SchemeShareButtonProps) {
  const shareData = {
    title: title,
    text: text,
    url: link, // Current URL
  };

  const handleShare = async () => {
    // Check if navigator.share is supported
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        // console.log("Shared successfully");
      } catch (err) {
        console.error("Error sharing:", err);
      }
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
    } else {
      alert("Web Share API not supported on this browser");
    }
  };

  return <Button onClick={handleShare}><ForwardIcon />{" "}Share Link</Button>;
}

export default SchemeShareButton;
