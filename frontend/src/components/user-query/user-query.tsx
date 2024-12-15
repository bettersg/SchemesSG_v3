import { Card, CardBody, CardFooter, CardHeader } from "@nextui-org/card";
import classes from './user-query.module.css';
import { useChat } from "@/app/providers";
import { Button, Tooltip, useDisclosure } from "@nextui-org/react";
import ResetQueryModal from "../reset-query-modal/reset-query-modal";
import { ResetIcon } from "@/assets/icons/reset-icon";

export default function UserQuery() {
    const { userQuery, setSchemes } = useChat();
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

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
            <CardHeader className={`justify-between ${classes.cardHeader}`}>
                <h4 className="text-small leading-none text-default-600" >Your query is:</h4>
                <Tooltip content="Reset Query" offset={-7}>
                    <Button onPress={onOpen} isIconOnly radius="full" size="sm" className={`${classes.resetButton}`}>
                        <ResetIcon />
                    </Button>
                </Tooltip>
                <ResetQueryModal isOpen={isOpen} onOpenChange={onOpenChange} handleReset={handleReset} />
            </CardHeader>
            <CardBody className={`${classes.cardBody}`}>
                <b>{userQuery}</b>
            </CardBody>
        </Card>
    )
}
