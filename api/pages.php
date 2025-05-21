<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Simple PHP API to serve page content
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

function getPageContent($pageNumber) {
    $fileName = sprintf("../extracted_content/raw_text/page_%04d.txt", $pageNumber);
    
    if (!file_exists($fileName)) {
        return null;
    }
    
    $content = file_get_contents($fileName);
    return [
        'pageNumber' => $pageNumber,
        'content' => $content,
        'wordCount' => str_word_count($content),
        'charCount' => strlen($content)
    ];
}

function searchContent($query, $maxResults = 20) {
    $results = [];
    $metadataFile = '../extracted_content/raw_text/metadata.json';
    
    if (!file_exists($metadataFile)) {
        return $results;
    }
    
    $metadata = json_decode(file_get_contents($metadataFile), true);
    $totalPages = $metadata['total_pages'];
    
    for ($i = 1; $i <= min($totalPages, 100); $i++) {
        $pageData = getPageContent($i);
        if ($pageData && stripos($pageData['content'], $query) !== false) {
            $pageData['title'] = getPageTitle($pageData['content'], $i);
            $pageData['preview'] = getPreview($pageData['content'], $query);
            $pageData['relevance'] = calculateRelevance($pageData['content'], $query);
            $results[] = $pageData;
            
            if (count($results) >= $maxResults) {
                break;
            }
        }
    }
    
    // Sort by relevance
    usort($results, function($a, $b) {
        return $b['relevance'] - $a['relevance'];
    });
    
    return $results;
}

function getPageTitle($content, $pageNumber) {
    $lines = explode("\n", $content);
    $title = '';
    
    foreach ($lines as $line) {
        $line = trim($line);
        if (strlen($line) > 10 && strlen($line) < 100) {
            $title = $line;
            break;
        }
    }
    
    if (empty($title)) {
        $title = "صفحة $pageNumber";
    }
    
    return $title;
}

function getPreview($content, $query) {
    $sentences = preg_split('/[.!?؟]/', $content);
    $bestMatch = '';
    $bestScore = 0;
    
    foreach ($sentences as $sentence) {
        $sentence = trim($sentence);
        if (strlen($sentence) < 20) continue;
        
        $score = substr_count(strtolower($sentence), strtolower($query));
        if ($score > $bestScore) {
            $bestScore = $score;
            $bestMatch = $sentence;
        }
    }
    
    return substr($bestMatch, 0, 200) . (strlen($bestMatch) > 200 ? '...' : '');
}

function calculateRelevance($content, $query) {
    $content = strtolower($content);
    $query = strtolower($query);
    $words = explode(' ', $query);
    $score = 0;
    
    foreach ($words as $word) {
        $score += substr_count($content, $word);
    }
    
    return $score;
}

// Handle API requests
$action = $_GET['action'] ?? 'page';

switch ($action) {
    case 'page':
        $pageNumber = (int)($_GET['page'] ?? 1);
        $pageData = getPageContent($pageNumber);
        
        if ($pageData) {
            echo json_encode($pageData);
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Page not found']);
        }
        break;
        
    case 'search':
        $query = $_GET['q'] ?? '';
        $maxResults = (int)($_GET['limit'] ?? 20);
        
        if (empty($query)) {
            echo json_encode(['error' => 'Query parameter required']);
            break;
        }
        
        $results = searchContent($query, $maxResults);
        echo json_encode([
            'query' => $query,
            'results' => $results,
            'count' => count($results)
        ]);
        break;
        
    case 'metadata':
        $metadataFile = '../extracted_content/raw_text/metadata.json';
        if (file_exists($metadataFile)) {
            echo file_get_contents($metadataFile);
        } else {
            echo json_encode(['error' => 'Metadata not found']);
        }
        break;
        
    case 'random':
        $count = (int)($_GET['count'] ?? 5);
        $metadataFile = '../extracted_content/raw_text/metadata.json';
        
        if (file_exists($metadataFile)) {
            $metadata = json_decode(file_get_contents($metadataFile), true);
            $totalPages = $metadata['total_pages'];
            $randomPages = [];
            
            for ($i = 0; $i < $count; $i++) {
                $randomPage = rand(1, $totalPages);
                $pageData = getPageContent($randomPage);
                if ($pageData) {
                    $pageData['title'] = getPageTitle($pageData['content'], $randomPage);
                    $randomPages[] = $pageData;
                }
            }
            
            echo json_encode($randomPages);
        } else {
            echo json_encode(['error' => 'Metadata not found']);
        }
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
        break;
}
?>