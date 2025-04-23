for i in {1..50}
do
    CSV_FILE="../../Data2/Logs2/gm/gm_simulation_log_$i.csv"
    echo "Testing $CSV_FILE"
    curl -s -X POST http://127.0.0.1:8000/ask_llm \
     -F "file=@${CSV_FILE}" > temp_response.json
    cat temp_response.json | awk -F'CLASSIFICATION: ' '/CLASSIFICATION:/ {
        split($2,a,"\\\\n"); 
        print a[1]
    }' >> output/gm_testing.txt
    sleep 10
done
rm temp_response.json
