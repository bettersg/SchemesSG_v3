#!/bin/bash

# Start Firebase functions only (connects to cloud Firestore for vector search)
# Note: Firestore emulator has limited vector search support
firebase emulators:start --only functions --project schemessg-v3-dev