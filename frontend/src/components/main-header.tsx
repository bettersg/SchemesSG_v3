"use client";
import { SendIcon } from "@/assets/icons/send-icon";
import logoImg from "@/assets/logo.jpg";
import {
  Button,
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
    { label: "About", href: "/about" },
    { label: "Feedback", href: "/feedback" },
    { label: "Contribute", href: "/contribute" },
  ];

  return (
    <Navbar
      isMenuOpen={isMenuOpen}
      onMenuOpenChange={setIsMenuOpen}
      classNames={{
        base: "bg-white",
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
              width={120}
              height={30}
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
        <NavbarItem className="hidden md:flex">
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
        </NavbarItem>

        {/* Telegram Bot Button - Mobile */}
        <NavbarItem className="md:hidden">
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
        </NavbarItem>

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
