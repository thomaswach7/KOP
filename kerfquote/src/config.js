// Einstellungen des Anbieters (also von Ihnen). Nach dem Ändern neu veröffentlichen.

export const CONFIG = {
  /**
   * Zahlungslink für die Pro-Lizenz, z. B. ein Stripe Payment Link oder eine
   * Lemon-Squeezy-/Paddle-Kaufseite. Leer = der Kaufen-Knopf zeigt "wird eingerichtet".
   */
  checkoutUrl: '',
  /** Maximale Dateigröße einer DXF-Datei in MB */
  maxFileMb: 25,
  /** Dateien, die "Beispielteile laden" öffnet (relativ zum Ordner samples/) */
  samples: ['flansch.dxf', 'halteblech.dxf'],
};
