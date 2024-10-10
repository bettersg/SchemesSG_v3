"use client";
import { useEffect, useState } from "react"; // Import useEffect and useState
import Link from "next/link";
import Image from "next/image";
import logoImg from "@/assets/logo.jpg";
import classes from "./main-header.module.css";
import {
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
} from "@nextui-org/navbar";
import { usePathname, useRouter } from "next/navigation";

type NavbarItem = {
  label: string;
  href: string;
};

export default function MainHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [hidden, setHidden] = useState(false);
  let lastScrollTop = 0;

  const navbarItems: NavbarItem[] = [
    { label: "Home", href: "/" },
    { label: "About", href: "/about" },
    { label: "Feedback", href: "/feedback" },
  ];

  useEffect(() => {
    const handleScroll = () => {
      const currentScroll =
        window.pageYOffset || document.documentElement.scrollTop;

      if (currentScroll > lastScrollTop) {
        // Scrolling down
        setHidden(true);
      } else {
        // Scrolling up
        setHidden(false);
      }
      lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const handleLinkClick = (href: string) => {
    router.push(href);
    window.scrollTo(0, 0);
  };

  return (
    <>
      <Navbar className={`${classes.navbar} ${hidden ? "hidden" : ""}`}>
        <NavbarBrand>
          <Link className={classes.logo} href="/">
            <Image
              src={logoImg}
              alt="Schemes SG logo"
              width={120}
              height={30}
              priority
            />
          </Link>
        </NavbarBrand>
        <NavbarContent className="hidden sm:flex gap-4" justify="end">
          {navbarItems.map((item, idx) => {
            return (
              <NavbarItem
                className={classes.navbarItem}
                key={idx}
                isActive={pathname === item.href ? true : undefined}
              >
                <Link
                  href={item.href}
                  onClick={() => handleLinkClick(item.href)}
                >
                  {item.label}
                </Link>
              </NavbarItem>
            );
          })}
        </NavbarContent>
      </Navbar>
    </>
  );
}
