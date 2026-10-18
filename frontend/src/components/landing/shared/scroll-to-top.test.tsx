import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ScrollToTop } from "./scroll-to-top";

function scrollWindowTo(y: number) {
  Object.defineProperty(window, "scrollY", { value: y, configurable: true });
  act(() => {
    window.dispatchEvent(new Event("scroll"));
  });
}

describe("ScrollToTop", () => {
  afterEach(() => {
    scrollWindowTo(0);
    vi.restoreAllMocks();
  });

  it("appears only once the reader is more than a screen down", () => {
    render(<ScrollToTop />);
    expect(screen.queryByRole("button", { name: "Scroll to top" })).toBeNull();

    scrollWindowTo(window.innerHeight + 1);
    expect(screen.getByRole("button", { name: "Scroll to top" })).toBeVisible();

    scrollWindowTo(10);
    expect(screen.queryByRole("button", { name: "Scroll to top" })).toBeNull();
  });

  it("returns the page to the top", () => {
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => {});
    render(<ScrollToTop />);
    scrollWindowTo(window.innerHeight * 3);

    fireEvent.click(screen.getByRole("button", { name: "Scroll to top" }));

    expect(scrollTo).toHaveBeenCalledWith(expect.objectContaining({ top: 0 }));
  });
});
