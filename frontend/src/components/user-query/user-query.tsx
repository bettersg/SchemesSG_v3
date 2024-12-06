import { Card, CardBody } from "@nextui-org/card";
import classes from './user-query.module.css';
import { useChat } from "@/app/providers";

export default function UserQuery() {
    const { userQuery } = useChat();

    return (
        <Card
            className={`${classes.card} ${classes.userQuery}`}
            fullWidth={false}
            radius="lg"
            shadow="none"
        >
            <CardBody className={`${classes.cardBody}`}>
                Your query is: <b>{userQuery}</b>
            </CardBody>
        </Card>
    )
}
