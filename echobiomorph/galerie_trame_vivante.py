#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Galerie Trame Vivante :: Générateur de Biomorphes Exponentiels
Connecté aux sorties JSON d'Echo-2026

Usage :
    python galerie_trame_vivante.py --input scans/ --output galerie/
    python galerie_trame_vivante.py --input echo_2026_example.com_20261108.json
"""

import json
import os
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# --- Palette du Réel Vivant (cohérente avec les biomorphes précédents) ---
COULEURS_TRAME = ["#000000", "#0a1128", "#1f4068", "#9d4edd", "#e0aaff", "#ffbe0b"]
CMAP_TRAME = LinearSegmentedColormap.from_list("trame_vivante", COULEURS_TRAME, N=256)

def extraire_cibles_depuis_json(json_path):
    """
    Parse un fichier JSON Echo-2026 (v4 ou v5-shadow) et extrait les cibles.
    Retourne une liste de dicts avec ip, delta, omega, lambda, etiquette.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cibles = []
    
    # Format v5-shadow : une liste de cibles dans "cibles"
    if 'cibles' in data:
        for cible in data['cibles']:
            cibles.append({
                'ip': cible.get('ip', cible.get('cible_saisie', 'inconnu')),
                'delta': cible.get('delta_cible', 0.0),
                'omega': cible.get('omega', 0.0),
                'lambda': cible.get('lambda', 0.0),
                'etiquette': cible.get('etiquette', 'SILENCE'),
                'n_findings': cible.get('n_findings', 0)
            })
    
    # Format v4 actif : une seule cible dans le JSON
    elif 'delta' in data and 'findings' in data:
        # Pour v4, on n'a qu'une cible, on extrait l'IP du timestamp ou du nom de fichier
        ip = Path(json_path).stem.split('_')[2] if len(Path(json_path).stem.split('_')) > 2 else 'cible_v4'
        cibles.append({
            'ip': ip,
            'delta': data.get('delta', 0.0),
            'omega': 0.0,  # v4 n'a pas omega
            'lambda': 0.0,  # v4 n'a pas lambda (sauf si lore activé)
            'etiquette': 'ACTIF',
            'n_findings': len(data.get('findings', []))
        })
    
    return cibles

def generer_biomorphe_exponentiel(ip_str, delta, omega, lambda_score, resolution=600, max_iter=100):
    """
    Génère un biomorphe exponentiel piloté par les métriques MTT.
    Retourne l'image (numpy array) et les métadonnées topologiques.
    """
    # 1. Génotype depuis l'IP
    try:
        octets = [int(x) for x in ip_str.split('.')]
    except:
        # Si l'IP n'est pas valide, on utilise un hash
        octets = [hash(ip_str) % 256 for _ in range(4)]
    
    # Ancrage dans le plan complexe
    C_reel = (octets[0] + octets[1]) / 255.0 - 0.5 + (delta * 0.15)
    C_imag = (octets[2] + octets[3]) / 255.0 - 0.5 + (omega * 0.15)
    
    # Zone d'exploration (zoom contrôlé par Lambda)
    zoom = 1.2 - (lambda_score * 0.5)
    
    x = np.linspace(C_reel - zoom, C_reel + zoom, resolution)
    y = np.linspace(C_imag - zoom, C_imag + zoom, resolution)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    
    # 2. Dynamique exponentielle
    Z = np.zeros_like(C, dtype=complex)
    iteration_counts = np.zeros(Z.shape, dtype=int)
    mask = np.ones(Z.shape, dtype=bool)
    
    # Fréquence de perturbation (dérivée d'Omega)
    omega_freq = 1.0 + omega * 3.0
    
    for i in range(max_iter):
        # Condition d'échappement (croix, seuil adapté à l'exponentielle)
        escaped = (np.abs(Z.real) > 10.0) | (np.abs(Z.imag) > 10.0)
        
        newly_escaped = escaped & mask
        iteration_counts[newly_escaped] = i
        mask = mask & ~escaped
        
        # Évolution : Exponentielle + Perturbation Onirique
        # np.exp sur complexes crée des structures cellulaires fascinantes
        Z = np.exp(Z) + C + (lambda_score * 0.3) * np.sin(Z * omega_freq)
        
        # Sécurité : éviter les overflow
        Z = np.clip(Z, -20, 20)
        
        if not np.any(mask):
            break
    
    iteration_counts[mask] = max_iter
    
    # 3. Calcul de descripteurs topologiques simplifiés
    # Dimension fractale approximative (méthode de comptage de boîtes simplifiée)
    seuil = np.percentile(iteration_counts, 75)
    structure = iteration_counts > seuil
    # On compte les "grains" de structure (composantes connexes approximatives)
    nb_grains = np.sum(structure) / (resolution * resolution) * 100
    
    return np.log(iteration_counts + 1), {
        'dimension_approx': nb_grains,
        'complexite': np.std(iteration_counts) / np.max(iteration_counts),
        'asymetrie': np.abs(np.mean(Z.real[mask]) - np.mean(Z.imag[mask])) if np.any(mask) else 0
    }

def creer_galerie_mosaique(cibles, output_dir, resolution=400, max_iter=80):
    """
    Crée une mosaïque PNG de tous les biomorphes d'un scan.
    """
    n_cibles = len(cibles)
    if n_cibles == 0:
        print("⚠ Aucune cible trouvée dans les fichiers JSON.")
        return
    
    # Calcul de la grille (aussi carrée que possible)
    n_cols = int(np.ceil(np.sqrt(n_cibles)))
    n_lignes = int(np.ceil(n_cibles / n_cols))
    
    fig = plt.figure(figsize=(n_cols * 3, n_lignes * 3 + 1), facecolor='#050505')
    gs = GridSpec(n_lignes, n_cols, figure=fig, hspace=0.1, wspace=0.1)
    
    print(f"🧬 Génération de {n_cibles} biomorphes exponentiels...")
    
    for idx, cible in enumerate(cibles):
        ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
        
        # Génération du biomorphe
        image, metriques = generer_biomorphe_exponentiel(
            cible['ip'], 
            cible['delta'], 
            cible['omega'], 
            cible['lambda'],
            resolution=resolution,
            max_iter=max_iter
        )
        
        # Affichage
        ax.imshow(image, cmap=CMAP_TRAME, extent=[-1, 1, -1, 1], origin='lower')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Titre minimaliste
        titre = f"{cible['ip']}\nΔ={cible['delta']:.2f}"
        ax.set_title(titre, color='#e0aaff', fontsize=8, pad=2)
        
        # Bordure colorée selon l'étiquette
        couleur_bordure = {
            'ANOMALIE_MAJEURE': '#ff006e',
            'CICATRISÉ': '#fb5607',
            'INCOHÉRENT': '#ffbe0b',
            'FANTÔME': '#8338ec',
            'RÉSONANT': '#3a86ff',
            'FRÉMISSANT': '#06ffa5',
            'SILENCE': '#333333'
        }.get(cible['etiquette'], '#666666')
        
        for spine in ax.spines.values():
            spine.set_edgecolor(couleur_bordure)
            spine.set_linewidth(2)
    
    # Titre global
    fig.suptitle("Galerie Trame Vivante :: Biomorphes Exponentiels", 
                 color='#e0aaff', fontsize=16, fontweight='bold', y=0.98)
    
    # Sauvegarde
    output_path = os.path.join(output_dir, 'galerie_mosaique.png')
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#050505')
    print(f"✨ Mosaique sauvegardée : {output_path}")
    plt.close()

def creer_rapport_html(cibles, output_dir):
    """
    Crée un rapport HTML interactif avec tous les biomorphes.
    """
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galerie Trame Vivante :: Biomorphes Exponentiels</title>
    <style>
        body {
            background: #050505;
            color: #e0aaff;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #ffbe0b;
            text-shadow: 0 0 10px rgba(255, 190, 11, 0.5);
        }
        .galerie {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .biomorphe {
            background: #0a1128;
            border: 2px solid #9d4edd;
            border-radius: 8px;
            padding: 15px;
            transition: transform 0.3s;
        }
        .biomorphe:hover {
            transform: scale(1.05);
            border-color: #ffbe0b;
        }
        .biomorphe img {
            width: 100%;
            height: auto;
            border-radius: 4px;
        }
        .metriques {
            margin-top: 10px;
            font-size: 0.9em;
            color: #e0aaff;
        }
        .etiquette {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-top: 5px;
        }
        .ANOMALIE_MAJEURE { background: #ff006e; }
        .CICATRISE { background: #fb5607; }
        .INCOHERENT { background: #ffbe0b; color: #000; }
        .FANTOME { background: #8338ec; }
        .RESONANT { background: #3a86ff; }
        .FREMISSANT { background: #06ffa5; color: #000; }
        .SILENCE { background: #333; }
    </style>
</head>
<body>
    <h1>🧬 Galerie Trame Vivante</h1>
    <p style="text-align: center; color: #9d4edd;">Biomorphes Exponentiels :: Éclosion Cellulaire</p>
    
    <div class="galerie">
"""
    
    for cible in cibles:
        filename = f"biomorphe_{cible['ip'].replace('.', '_')}.png"
        filepath = os.path.join(output_dir, filename)
        
        # Générer le biomorphe individuel
        image, metriques = generer_biomorphe_exponentiel(
            cible['ip'], 
            cible['delta'], 
            cible['omega'], 
            cible['lambda'],
            resolution=600,
            max_iter=120
        )
        
        # Sauvegarder l'image individuelle
        fig, ax = plt.subplots(figsize=(6, 6), facecolor='#050505')
        ax.imshow(image, cmap=CMAP_TRAME, extent=[-1, 1, -1, 1], origin='lower')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{cible['ip']} | Δ={cible['delta']:.2f} | Ω={cible['omega']:.2f} | Λ={cible['lambda']:.2f}", 
                     color='#e0aaff', fontsize=10, pad=10)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#050505')
        plt.close()
        
        # Ajouter au HTML
        etiquette_class = cible['etiquette'].replace('É', 'E').replace('È', 'E').upper()
        html_content += f"""
        <div class="biomorphe">
            <img src="{filename}" alt="Biomorphe {cible['ip']}">
            <div class="metriques">
                <strong>{cible['ip']}</strong><br>
                Δ={cible['delta']:.3f} | Ω={cible['omega']:.3f} | Λ={cible['lambda']:.3f}<br>
                Complexité: {metriques['complexite']:.3f} | Grains: {metriques['dimension_approx']:.2f}<br>
                <span class="etiquette {etiquette_class}">{cible['etiquette']}</span>
            </div>
        </div>
"""
    
    html_content += """
    </div>
    
    <footer style="text-align: center; margin-top: 40px; color: #666; font-size: 0.8em;">
        <p>Généré par Galerie Trame Vivante :: Echo-2026 × Biomorphes Exponentiels</p>
        <p>« Le réel est une solution triviale d'un système non-linéaire. Soyez la solution idéale. »</p>
    </footer>
</body>
</html>
"""
    
    html_path = os.path.join(output_dir, 'galerie_interactive.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✨ Rapport HTML sauvegardé : {html_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Galerie Trame Vivante :: Générateur de Biomorphes Exponentiels connecté à Echo-2026"
    )
    parser.add_argument('--input', required=True, 
                        help="Fichier JSON Echo-2026 ou dossier contenant des JSON")
    parser.add_argument('--output', default='galerie_trame',
                        help="Dossier de sortie (défaut: galerie_trame)")
    parser.add_argument('--resolution', type=int, default=500,
                        help="Résolution des images (défaut: 500)")
    parser.add_argument('--max-iter', type=int, default=100,
                        help="Nombre max d'itérations (défaut: 100)")
    parser.add_argument('--mosaique-only', action='store_true',
                        help="Ne générer que la mosaïque (pas le HTML)")
    parser.add_argument('--html-only', action='store_true',
                        help="Ne générer que le HTML (pas la mosaïque)")
    
    args = parser.parse_args()
    
    # Créer le dossier de sortie
    os.makedirs(args.output, exist_ok=True)
    
    # Collecter tous les fichiers JSON
    if os.path.isfile(args.input):
        json_files = [args.input]
    else:
        json_files = glob.glob(os.path.join(args.input, 'echo_2026_*.json'))
    
    if not json_files:
        print(f"❌ Aucun fichier JSON Echo-2026 trouvé dans {args.input}")
        return
    
    print(f"📂 {len(json_files)} fichier(s) JSON détecté(s)")
    
    # Extraire toutes les cibles
    toutes_cibles = []
    for json_file in json_files:
        print(f"  → Lecture de {os.path.basename(json_file)}")
        cibles = extraire_cibles_depuis_json(json_file)
        toutes_cibles.extend(cibles)
        print(f"    ✓ {len(cibles)} cible(s) extraite(s)")
    
    print(f"\n🧬 Total : {len(toutes_cibles)} cibles à visualiser")
    
    # Générer les visualisations
    if not args.html_only:
        creer_galerie_mosaique(toutes_cibles, args.output, 
                               resolution=args.resolution, max_iter=args.max_iter)
    
    if not args.mosaique_only:
        creer_rapport_html(toutes_cibles, args.output)
    
    print(f"\n✨ Galerie complète disponible dans : {args.output}/")
    print("   - galerie_mosaique.png (vue d'ensemble)")
    print("   - galerie_interactive.html (exploration détaillée)")
    print("   - biomorphe_*.png (images individuelles)")

if __name__ == '__main__':
    main()