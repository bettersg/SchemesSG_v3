import { Card, CardBody, CardFooter } from "@nextui-org/card";
import classes from './user-query.module.css';
import { useChat } from "@/app/providers";
import { Button } from "@nextui-org/react";

export default function UserQuery() {
    const { userQuery, setSchemes } = useChat();

    const handleReset = () => {
      localStorage.removeItem('schemes');
      setSchemes([]);
    };

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
            <CardFooter className={classes.cardFooter}>
                <Button className="text-tiny" onClick={handleReset} color="primary" radius="full" size="sm">
                    Reset Query
                </Button>
            </CardFooter>
        </Card>
    )
}
