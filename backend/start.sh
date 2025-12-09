#!/bin/bash

# Enable debug logging for firebase emulator
# export FIREBASE_DEBUG=true

# Start Firebase emulator with debug logging
# firebase emulators:start --only functions --project schemessg-v3-dev --debug
firebase emulators:start --only functions,firestore --project schemessg-v3-dev --debug