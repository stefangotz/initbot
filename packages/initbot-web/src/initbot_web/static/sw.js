// SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
