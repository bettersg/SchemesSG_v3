"use client";
import logoImg from "@/assets/logo.jpg";
import {
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  NavbarMenu,
  NavbarMenuItem,
  NavbarMenuToggle,
} from "@nextui-org/navbar";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { HamburgerIcon } from "../../assets/icons/hamburger-icon";
import classes from "./main-header.module.css";

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
  ];

  return (
    <>
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
            "data-[active=true]:after:bottom-0",
            "data-[active=true]:after:left-0",
            "data-[active=true]:after:right-0",
            "data-[active=true]:after:h-[2px]",
            "data-[active=true]:after:rounded-[2px]",
            "data-[active=true]:after:bg-blue-500",
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
            "data-[active=true]:text-blue-600",
            "data-[active=true]:font-medium",
          ],
        }}
      >
        <NavbarContent>
          <NavbarBrand>
            <a className={classes.logo} href="/">
              <Image
                src={logoImg}
                alt="Schemes SG logo"
                width={120}
                height={30}
                priority
              />
            </a>
          </NavbarBrand>
          <NavbarMenuToggle
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            className="sm:hidden text-gray-700 hover:bg-gray-100 p-1 rounded-lg transition-colors"
            icon={<HamburgerIcon />}
          />
        </NavbarContent>

        <NavbarContent className="hidden sm:flex gap-4" justify="end">
          {navbarItems.map((item, idx) => (
            <NavbarItem
              className={`${classes.navbarItem} hover:text-blue-600 transition-colors`}
              key={idx}
              isActive={pathname === item.href}
            >
              <Link href={item.href}>{item.label}</Link>
            </NavbarItem>
          ))}
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
                    ? "text-blue-600 font-medium"
                    : "text-gray-700"
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
    </>
  );
}
