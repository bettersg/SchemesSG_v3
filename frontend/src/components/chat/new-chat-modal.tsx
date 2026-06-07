"use client";

import { Button, Modal } from "@heroui/react";
import {
  productButtonDefault,
  productButtonOutlineNeutral,
  productButtonSolidAmber,
} from "@/lib/design-system/product-styles";

type NewChatModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  handleReset: () => void;
};

export default function NewChatModal({
  isOpen,
  onOpenChange,
  handleReset,
}: NewChatModalProps) {
  return (
    <Modal.Backdrop isOpen={isOpen} onOpenChange={onOpenChange}>
      <Modal.Container>
        <Modal.Dialog className="bg-white text-(--schemes-ink)">
          <Modal.Header>
            <Modal.Heading className="text-lg font-semibold text-(--schemes-blue-900)">
              New Chat
            </Modal.Heading>
          </Modal.Header>
          <Modal.Body>
            <p className="text-(--schemes-muted)">
              Are you sure you want to start a new chat? Your chat history and
              search results will be reset.
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="outline"
              className={`${productButtonOutlineNeutral} ${productButtonDefault}`}
              onPress={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className={`${productButtonSolidAmber} ${productButtonDefault}`}
              onPress={handleReset}
            >
              Confirm
            </Button>
          </Modal.Footer>
        </Modal.Dialog>
      </Modal.Container>
    </Modal.Backdrop>
  );
}
