<?php

function splitInfoColumnFromDirectory($directory, $outputDirectory)
{
    if (!is_dir($directory)) {
        echo "Указанный каталог $directory не существует.\n";
        return;
    }

    if (!is_dir($outputDirectory)) {
        mkdir($outputDirectory, 0777, true);
    }

    $files = glob($directory . DIRECTORY_SEPARATOR . "*.csv");

    if (empty($files)) {
        echo "В каталоге $directory не найдено файлов CSV.\n";
        return;
    }

    foreach ($files as $inputFile) {
        $fileName = pathinfo($inputFile, PATHINFO_FILENAME);
        $outputFile = $outputDirectory . DIRECTORY_SEPARATOR . $fileName . "_processed.csv";
        splitInfoColumn($inputFile, $outputFile);
    }

    echo "Обработка всех файлов завершена. Результаты сохранены в каталоге $outputDirectory.\n";
}

function splitInfoColumn($inputFile, $outputFile)
{
    $rows = [];
    $newColumns = [];

    if (($handle = fopen($inputFile, "r")) !== false) {
        $header = fgetcsv($handle, 0, ";");

        // Проверка на "фейковые" заголовки
        $isFakeHeader = true;
        foreach ($header as $column) {
            if (!preg_match('/^Column\d+$/', $column)) {
                $isFakeHeader = false;
                break;
            }
        }
        if ($isFakeHeader) {
            $header = fgetcsv($handle, 0, ";");
        }

        // --- первый проход: собираем все строки и новые колонки ---
        while (($data = fgetcsv($handle, 0, ";")) !== false) {
            $row = array_combine($header, $data);

            $infoJson = $row['info'] ?? '';
            $parsedInfo = json_decode($infoJson, true);
            if (!is_array($parsedInfo)) {
                $parsedInfo = [];
            }

            // собираем все новые колонки
            foreach ($parsedInfo as $key => $value) {
                if (!in_array($key, $newColumns)) {
                    $newColumns[] = $key;
                }
            }

            // временно сохраняем массив строки + parsed info
            $row['_parsed_info'] = $parsedInfo;
            $rows[] = $row;
        }

        fclose($handle);

        // --- финальный заголовок ---
        $finalHeader = array_merge($header, $newColumns);

        $outputHandle = fopen($outputFile, "w");
        fputcsv($outputHandle, $finalHeader, ";");

        // --- второй проход: записываем строки, подставляя значения JSON ---
        foreach ($rows as $row) {
            $line = [];
            foreach ($finalHeader as $column) {
                if ($column === 'info') {
                    $line[] = $row['info'] ?? '';
                } elseif (isset($row['_parsed_info'][$column])) {
                    $line[] = $row['_parsed_info'][$column];
                } else {
                    $line[] = $row[$column] ?? '';
                }
            }
            fputcsv($outputHandle, $line, ";");
        }

        fclose($outputHandle);

        echo "Файл $inputFile успешно обработан и сохранён в $outputFile.\n";
    } else {
        echo "Не удалось открыть файл $inputFile\n";
    }
}



$directory = "files/sensoren_new"; // Путь к каталогу с исходными файлами
$outputDirectory = "files/sensoren_new/processed"; // Путь к каталогу для сохранения обработанных файлов
splitInfoColumnFromDirectory($directory, $outputDirectory);
