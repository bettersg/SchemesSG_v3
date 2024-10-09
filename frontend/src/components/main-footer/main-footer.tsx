import Link from "next/link";
import classes from "./main-footer.module.css";
import {Divider} from "@nextui-org/divider";

const data = [
    {
        title: "Info",
        links: [
            { label: "About", link: "/about" },
            { label: "Our Team", link: "/team" },
            { label: "Blog", link: "/blog" }
        ]
    },
    {
        title: "Contact",
        links: [
            { label: "Feedback", link: "/feedback" },
            { label: "Contribute", link: "/contribute" }
        ]
    }
]

export default function MainFooter() {

    const groups = data.map(group => {
        const links = group.links.map((link, idx) => {
            return <Link key={idx} href={link.link} className={classes.link}>{link.label}</Link>
        })

        return (
            <div className={classes.wrapper} key={group.title}>
                <p className={classes.title}>{group.title}</p>
                {links}
            </div>
        )
    })

    return (
        <footer className={classes.footer}>
            <div className={classes.inner}>
                <div className={classes.groups}>{groups}</div>
            </div>
            <Divider orientation="vertical" className="divide-white" />
            <p className="text-xs">© 2021 Schemes SG.</p>
        </footer>
    )
}
