#!/bin/bash

# Script to rename folders to lowercase and update references
# Run this from the repository root

echo "🔄 Renaming folders to lowercase..."

# Rename directories
if [ -d "V0_Initial_Flow" ]; then
    mv "V0_Initial_Flow" "v0_initial_flow"
    echo "✅ Renamed V0_Initial_Flow → v0_initial_flow"
fi

if [ -d "V1_Linear_Flow" ]; then
    mv "V1_Linear_Flow" "v1_linear_flow"
    echo "✅ Renamed V1_Linear_Flow → v1_linear_flow"
fi

if [ -d "V1.5_Enhanced_Verification" ]; then
    mv "V1.5_Enhanced_Verification" "v1.5_enhanced_verification"
    echo "✅ Renamed V1.5_Enhanced_Verification → v1.5_enhanced_verification"
fi

if [ -d "V2_Modular_Expansion" ]; then
    mv "V2_Modular_Expansion" "v2_modular_expansion"
    echo "✅ Renamed V2_Modular_Expansion → v2_modular_expansion"
fi

if [ -d "V3_Intent_Driven_Minimalism" ]; then
    mv "V3_Intent_Driven_Minimalism" "v3_intent_driven_minimalism"
    echo "✅ Renamed V3_Intent_Driven_Minimalism → v3_intent_driven_minimalism"
fi

echo "🔄 Updating README references..."

# Update main README.md
if [ -f "README.md" ]; then
    sed -i 's/V0_Initial_Flow/v0_initial_flow/g' README.md
    sed -i 's/V1_Linear_Flow/v1_linear_flow/g' README.md
    sed -i 's/V1.5_Enhanced_Verification/v1.5_enhanced_verification/g' README.md
    sed -i 's/V2_Modular_Expansion/v2_modular_expansion/g' README.md
    sed -i 's/V3_Intent_Driven_Minimalism/v3_intent_driven_minimalism/g' README.md
    echo "✅ Updated main README.md"
fi

# Update individual README files
for readme in */README.md; do
    if [ -f "$readme" ]; then
        sed -i 's/V0_Initial_Flow/v0_initial_flow/g' "$readme"
        sed -i 's/V1_Linear_Flow/v1_linear_flow/g' "$readme"
        sed -i 's/V1.5_Enhanced_Verification/v1.5_enhanced_verification/g' "$readme"
        sed -i 's/V2_Modular_Expansion/v2_modular_expansion/g' "$readme"
        sed -i 's/V3_Intent_Driven_Minimalism/v3_intent_driven_minimalism/g' "$readme"
        echo "✅ Updated $readme"
    fi
done

echo "🎉 Folder renaming and README updates complete!"
echo ""
echo "Next steps:"
echo "1. git add ."
echo "2. git commit -m 'Rename folders to lowercase and update references'"
echo "3. git push origin master"
