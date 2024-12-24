import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";

type ResetQueryModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  handleReset: () => void;
};

export default function ResetQueryModal({
  isOpen,
  onOpenChange,
  handleReset,
}: ResetQueryModalProps) {
  return (
    <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader className="flex flex-col gap-1">
              Reset Search
            </ModalHeader>
            <ModalBody>
              <p>
                Are you sure you want to reset your search? Your chat history
                and search results will be reset.
              </p>
            </ModalBody>
            <ModalFooter>
              <Button color="danger" variant="light" onPress={onClose}>
                Cancel
              </Button>
              <Button color="primary" onPress={handleReset}>
                Confirm
              </Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
