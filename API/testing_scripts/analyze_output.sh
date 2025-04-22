# Count and display errors with cleaner formatting
echo "Number of incorrect Battery Drain tests: $(cat output/bd_testing.txt | grep -v "Battery Drain" | wc -l | tr -d ' ') / $(ls "../../Data2/Logs2/bd" | wc -l | tr -d ' ')"
echo "Number of incorrect DOS tests: $(cat output/dos_testing.txt | grep -v "Denial of Service" | wc -l | tr -d ' ') / $(ls "../../Data2/Logs2/dos" | wc -l | tr -d ' ')"
echo "Number of incorrect MITM tests: $(cat output/mitm_testing.txt | grep -v "Man-in-the-Middle" | wc -l | tr -d ' ') / $(ls "../../Data2/Logs2/mitm" | wc -l | tr -d ' ')"
echo "Number of incorrect GM tests: $(cat output/gm_testing.txt | grep -v "Grid Manipulation" | wc -l | tr -d ' ') / $(ls "../../Data2/Logs2/gm" | wc -l | tr -d ' ')"
echo "Number of incorrect Clean tests: $(cat output/clean_testing.txt | grep -v "Clean" | wc -l | tr -d ' ') / $(ls "../../Data2/Logs2/clean" | wc -l | tr -d ' ')"
