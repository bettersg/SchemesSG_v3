"use client"

import { Button, Modal } from "@heroui/react";
import {
	productButtonMd,
	productButtonPrimary,
	productButtonTertiary,
} from "@/lib/design-system/product-styles";

type ResetQueryModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  handleReset: () => void;
};

export default function ResetQueryModal({ isOpen, onOpenChange, handleReset }: ResetQueryModalProps) {
  return (
    <Modal.Backdrop isOpen={isOpen} onOpenChange={onOpenChange}>
      <Modal.Container>
        <Modal.Dialog className="bg-white text-(--schemes-ink)">
          <Modal.Header>
            <Modal.Heading className="text-lg font-semibold text-(--schemes-blue-900)">
              Reset Search
            </Modal.Heading>
          </Modal.Header>
          <Modal.Body>
            <p className="text-(--schemes-muted)">
              Are you sure you want to reset your search? Your chat history and
              search results will be reset.
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="outline"
              className={`${productButtonTertiary} ${productButtonMd}`}
              onPress={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className={`${productButtonPrimary} ${productButtonMd}`}
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
