for i in scripts/*
do
    sh $i
done
sh analyze_output.sh
