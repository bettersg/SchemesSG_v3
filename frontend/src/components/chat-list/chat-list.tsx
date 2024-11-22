import { Avatar, Card, CardBody } from "@nextui-org/react";
import classes from "./chat-list.module.css"
import ReactMarkdown from "react-markdown";
import { Message } from "@/app/providers";

interface ChatListProps {
    messages: Message[];
}

export default function ChatList({ messages }: ChatListProps) {

    return (
        <div className={classes.chatList}>
          {messages.map((msg, index) => (
            <div key={index} className={`${classes.messageContainer} ${msg.type === "user" ? classes.userContainer : classes.botContainer}`}>
              {msg.type === "bot" && (
                <Avatar
                  name="S"
                  size="sm"
                  className={classes.avatar}
                />
              )}
              <Card
                className={`${classes.card} ${msg.type === "user" ? classes.user : classes.bot}`}
                fullWidth={false}
                radius="lg"
                shadow="none"
              >
                <CardBody className={classes.cardBody}>
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </CardBody>
              </Card>
            </div>
          ))}
        </div>
    );
}
