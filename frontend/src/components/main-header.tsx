<<<<<<< HEAD
"use client";
import logoImg from "@/assets/logo.svg";
import {
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  NavbarMenu,
  NavbarMenuItem,
  NavbarMenuToggle,
} from "@heroui/react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { HamburgerIcon } from "../assets/icons/hamburger-icon";
import clsx from "clsx";

type NavbarItem = {
  label: string;
  href: string;
};

export default function MainHeader() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navbarItems: NavbarItem[] = [
    { label: "Home", href: "/" },
    { label: "Feedback", href: "/feedback" },
    { label: "Contribute", href: "/contribute" },
  ];

  return (
    <Navbar
      isMenuOpen={isMenuOpen}
      onMenuOpenChange={setIsMenuOpen}
      classNames={{
        base: "bg-white shadow-sm",
        wrapper: "px-4 sm:px-6",
        item: [
          "flex",
          "relative",
          "h-full",
          "items-center",
          "data-[active=true]:after:content-['']",
          "data-[active=true]:after:absolute",
          "data-[active=true]:after:bottom-2",
          "data-[active=true]:after:left-0",
          "data-[active=true]:after:right-0",
          "data-[active=true]:after:h-[2px]",
          "data-[active=true]:after:rounded-[2px]",
          "data-[active=true]:after:bg-schemes-blue",
          "data-[active=true]:text-schemes-blue",
        ],
        menuItem: [
          "flex",
          "flex-col",
          "gap-2",
          "py-4",
          "px-6",
          "hover:bg-gray-50",
          "transition-colors",
          "rounded-lg",
          "data-[active=true]:bg-blue-50",
          "data-[active=true]:text-schemes-blue",
          "data-[active=true]:font-medium",
        ],
      }}
    >
      <NavbarContent>
        <NavbarBrand>
          <Link href="/">
            <Image
              src={logoImg}
              alt="Schemes SG logo"
              width={160}
              unoptimized
              priority
            />
          </Link>
        </NavbarBrand>
      </NavbarContent>

      <NavbarContent className="hidden md:flex gap-4" justify="center">
        {navbarItems.map((item, idx) => (
          <NavbarItem
            className="text-schemes-gray font-medium hover:font-semibold hover:text-schemes-blue transition-colors"
            key={idx}
            isActive={pathname === item.href}
          >
            <Link href={item.href}>{item.label}</Link>
          </NavbarItem>
        ))}
      </NavbarContent>

      <NavbarContent justify="end">
        {/* Telegram Bot Button - Desktop */}
        {/* <NavbarItem className="hidden md:flex">
          <Button
            as={Link}
            href="https://t.me/SchemesSGBot"
            target="_blank"
            rel="noopener noreferrer"
            className="border-2 border-gray-100 bg-white text-blue-500 hover:text-white px-4 py-2 rounded-full hover:bg-schemes-blue transition-colors group"
          >
            <SendIcon className="text-blue-500 group-hover:text-white transition-colors" />
            <span className="ml-0 font-semibold">SchemesSGBot</span>
          </Button>
        </NavbarItem> */}

        {/* Telegram Bot Button - Mobile */}
        {/* <NavbarItem className="md:hidden">
          <Link
            href="https://t.me/SchemesSGBot"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center"
          >
            <Button
              size="sm"
              className="border-2 border-gray-100 bg-white text-blue-500 hover:text-white px-4 py-2 rounded-full hover:bg-blue-600 transition-colors group"
            >
              <SendIcon className="text-blue-500 group-hover:text-white transition-colors" />
              <span className="ml-0 font-semibold">SchemesSGBot</span>
            </Button>
          </Link>
        </NavbarItem> */}

        <NavbarMenuToggle
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          className={clsx(
            "md:hidden w-min h-min p-1 rounded-lg",
            "text-gray-700 hover:bg-gray-100 transition-colors"
          )}
          icon={<HamburgerIcon size={32}/>}
        />
      </NavbarContent>

      <NavbarMenu className="pt-6 bg-white/80 backdrop-blur-md">
        {navbarItems.map((item, idx) => (
          <NavbarMenuItem
            key={`${item.label}-${idx}`}
            isActive={pathname === item.href}
          >
            <Link
              className={`w-full text-lg ${
                pathname === item.href
                  ? "text-schemes-blue font-medium"
                  : "text-schemes-darkblue"
              }`}
              href={item.href}
              onClick={() => setIsMenuOpen(false)}
            >
              {item.label}
            </Link>
          </NavbarMenuItem>
        ))}
      </NavbarMenu>
    </Navbar>
  );
}
=======
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";
import Image from "next/image";

const SchemesSGLogo = () => (
	<div className="w-full h-8">
		<Image className="h-full" src='logo.svg' alt="Schemes.sg logo" width={16} height={32}/>
	</div>
);

type NavItem = { label: string; href: string };

export default function MainHeader() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems: NavItem[] = [
    { label: "Home", href: "/" },
    { label: "Explore", href: "/explore" },
    { label: "Feedback", href: "/feedback" },
    { label: "Contribute", href: "/contribute" },
  ];

  return (
    <header className="bg-white border-b border-[#e8eef6] w-full h-[60px] z-50">
      <div className="px-4 sm:px-6 lg:px-10 max-w-[1280px] mx-auto flex items-center justify-between h-full">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <SchemesSGLogo />
          <span className="font-[var(--font-head)] font-bold text-[16px] text-[#185FA5]">
            Schemes<span className="text-[#EF9F27]">SG</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                pathname === item.href
                  ? "text-[#185FA5] bg-[#E6F1FB]"
                  : "text-[#5F5E5A] hover:text-[#185FA5] hover:bg-[#E6F1FB]"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Desktop CTA + mobile hamburger */}
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-[10px] bg-[#EF9F27] text-white text-sm font-semibold transition-all hover:bg-[#BA7517]"
          >
            Find Schemes
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M14 7H0M8 1l6 6-6 6" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <button
            className="md:hidden flex items-center justify-center p-2 text-[#444441]"
            onClick={() => setIsMenuOpen((o) => !o)}
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMenuOpen ? (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 4l12 12M16 4L4 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden pt-4 pb-4 px-4 bg-white/95 backdrop-blur-md border-t border-[#e8eef6] flex flex-col gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setIsMenuOpen(false)}
              className={clsx(
                "block w-full px-4 py-3 rounded-xl text-base font-medium transition-colors",
                pathname === item.href
                  ? "text-[#185FA5] bg-[#E6F1FB]"
                  : "text-[#444441] hover:bg-[#F1EFE8]"
              )}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/"
            onClick={() => setIsMenuOpen(false)}
            className="block w-full px-4 py-3 mt-2 rounded-xl text-base font-semibold text-center bg-[#EF9F27] text-white"
          >
            Find Schemes →
          </Link>
        </div>
      )}
    </header>
  );
}
>>>>>>> 5bcdda1 (New design initial draft)
