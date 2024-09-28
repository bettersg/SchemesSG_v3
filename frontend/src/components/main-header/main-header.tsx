'use client';
import Link from "next/link";
import Image from "next/image";
import logoImg from "@/assets/logo.jpg"
import classes from './main-header.module.css';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem } from "@nextui-org/navbar";
import { usePathname } from "next/navigation";

type NavbarItem = {
    label: string,
    href: string
}

export default function MainHeader() {
    const pathname = usePathname();

    const navbarItems: NavbarItem[] = [
        { label: "Home", href: "/" },
        { label: "About", href: "/about" },
        { label: "Feedback", href: "/feedback" }
    ]

    return (
        <>
            <Navbar
                classNames={{
                    item: [
                    "flex",
                    "relative",
                    "h-full",
                    "items-center",
                    "data-[active=true]:after:bg-primary",
                    "data-[active=true]:after:text-blue-600",
                    "data-[active=true]:after:font-extrabold",
                    ],
                }}
            >
                <NavbarBrand>
                    <Link className={classes.logo} href="/">
                        <Image src={logoImg} alt="Schemes SG logo" width={120} height={30} priority/>
                    </Link>
                </NavbarBrand>
                <NavbarContent className="hidden sm:flex gap-4" justify="end">
                    {navbarItems.map((item, idx) => {
                        return (
                            <NavbarItem className={classes.navbarItem} key={idx} isActive={pathname === item.href ? true : undefined}>
                                <Link href={item.href}>{item.label}</Link>
                            </NavbarItem>
                        )
                    })}
                </NavbarContent>
            </Navbar>
        </>
    )
}
