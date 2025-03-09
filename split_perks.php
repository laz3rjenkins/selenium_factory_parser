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
    $tempFile = "temp_input.csv";
    $content = file_get_contents($inputFile);
    file_put_contents($tempFile, $content);

    if (($handle = fopen($tempFile, "r")) !== false) {
        $header = fgetcsv($handle, 0, ";");

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

        $rows = [];
        $newColumns = [];

        while (($data = fgetcsv($handle, 0, ";")) !== false) {
            $row = array_combine($header, $data);
            $info = $row['info'] ?? '';

            $infoParts = explode(";", $info);
            $parsedInfo = [];

            for ($i = 0; $i < count($infoParts); $i += 2) {
                if (isset($infoParts[$i + 1])) {
                    $key = trim($infoParts[$i]);
                    $value = trim($infoParts[$i + 1]);
                    $parsedInfo[$key] = $value;
                    if (!in_array($key, $newColumns)) {
                        $newColumns[] = $key;
                    }
                }
            }

            $row = array_merge($row, $parsedInfo);
            $rows[] = $row;
        }

        fclose($handle);

        $outputHandle = fopen($outputFile, "w");

        $header = array_merge($header, $newColumns);
        fputcsv($outputHandle, $header, ";");

        foreach ($rows as $row) {
            $line = [];
            foreach ($header as $column) {
                $line[] = $row[$column] ?? '';
            }
            fputcsv($outputHandle, $line, ";");
        }

        fclose($outputHandle);

        unlink($tempFile);

        echo "Файл $inputFile успешно обработан и сохранён в $outputFile.\n";
    } else {
        echo "Не удалось открыть файл $tempFile\n";
    }
}

$directory = "files/sensoren_new"; // Путь к каталогу с исходными файлами
$outputDirectory = "files/sensoren_new/processed"; // Путь к каталогу для сохранения обработанных файлов
splitInfoColumnFromDirectory($directory, $outputDirectory);
