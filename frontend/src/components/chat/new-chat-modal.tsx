"use client";

import { Button, Modal } from "@heroui/react";
import { Trans } from "@lingui/react/macro";
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
              <Trans comment="Heading of the dialog that confirms starting a new chat">
                New Chat
              </Trans>
            </Modal.Heading>
          </Modal.Header>
          <Modal.Body>
            <p className="text-(--schemes-muted)">
              <Trans>
                Are you sure you want to start a new chat? Your chat history and
                search results will be reset.
              </Trans>
            </p>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="outline"
              className={`${productButtonOutlineNeutral} ${productButtonDefault}`}
              onPress={() => onOpenChange(false)}
            >
              <Trans>Cancel</Trans>
            </Button>
            <Button
              variant="primary"
              className={`${productButtonSolidAmber} ${productButtonDefault}`}
              onPress={handleReset}
            >
              <Trans comment="Confirms starting a new chat, which clears the current one">
                Confirm
              </Trans>
            </Button>
          </Modal.Footer>
        </Modal.Dialog>
      </Modal.Container>
    </Modal.Backdrop>
  );
}
