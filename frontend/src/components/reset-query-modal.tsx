<<<<<<< HEAD
import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/react";

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
=======
"use client"

import { Button, Modal } from "@heroui/react";

type ResetQueryModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  handleReset: () => void;
};

export default function ResetQueryModal({ isOpen, onOpenChange, handleReset }: ResetQueryModalProps) {
  return (
	<Modal>
		<Modal.Backdrop isOpen={isOpen} onOpenChange={onOpenChange}>
			<Modal.Container>
				<Modal.Dialog>
					<Modal.Header>
						<Modal.Heading className="text-lg font-semibold">
							Reset Search
						</Modal.Heading>
					</Modal.Header>
					<Modal.Body>
						<p>
						Are you sure you want to reset your search? Your chat history and search results will be
						reset.
						</p>
					</Modal.Body>
					<Modal.Footer>
						<>
							<Button variant="danger-soft" onPress={() => onOpenChange(false)}>
								Cancel
							</Button>
							<Button onPress={handleReset}>
								Confirm
							</Button>
						</>
					</Modal.Footer>
				</Modal.Dialog>
			</Modal.Container>
		</Modal.Backdrop>
	</Modal>
  );
}
>>>>>>> 5bcdda1 (New design initial draft)
