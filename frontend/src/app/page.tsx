import MainChat from "@/components/main-chat/main-chat";
import { Spacer } from "@nextui-org/react";
import SchemesList from "@/components/schemes/schemes-list"

export default function Home() {
    return (
        <main>
            <MainChat />
            <Spacer y={6} />
            <SchemesList />
        </main>
    )
}
