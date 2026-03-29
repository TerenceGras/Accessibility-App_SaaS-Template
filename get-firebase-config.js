#!/usr/bin/env node

/**
 * Firebase Config Helper for LumTrails
 * 
 * This script helps you get the Firebase configuration for your web app.
 * Run this after setting up Firebase Auth in the console.
 */

console.log(`
🔥 Firebase Configuration Setup for LumTrails
=============================================

To get your Firebase configuration:

1. Open Firebase Console: https://console.firebase.google.com/project/YOUR_PROJECT_ID/settings/general/

2. Scroll down to "Your apps" section

3. If no web app exists:
   - Click "Add app" → Web icon (</>)
   - Register app name: "LumTrails Web App"
   - Skip hosting setup (we use Cloud Run)

4. Copy the firebaseConfig object that looks like this:

   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
     projectId: "YOUR_PROJECT_ID",
     storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
     messagingSenderId: "123456789012",
     appId: "1:123456789012:web:abc..."
   };

5. Replace the placeholder values in:
   ./web/src/config/firebase.js

6. Enable Authentication:
   - Go to: https://console.firebase.google.com/project/YOUR_PROJECT_ID/authentication/providers
   - Enable "Email/Password" authentication
   - Optionally enable "Google" for easier B2B access

🚀 Then you're ready to deploy!

`);

// Check if we can get project info
const { exec } = require('child_process');

exec('gcloud config get-value project', (error, stdout, stderr) => {
  if (error) {
    console.log('⚠️  Make sure you\'re logged into gcloud CLI');
    return;
  }
  
  const projectId = stdout.trim();
  console.log(`✅ Current project: ${projectId}`);
  
  if (projectId === 'YOUR_PROJECT_ID') {
    console.log(`
📋 Quick Links for ${projectId}:
• Console: https://console.firebase.google.com/project/${projectId}
• Auth: https://console.firebase.google.com/project/${projectId}/authentication
• Settings: https://console.firebase.google.com/project/${projectId}/settings/general/
`);
  }
});
